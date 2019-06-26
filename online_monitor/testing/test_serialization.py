''' Check the serialization utils for complex data structures
'''
import unittest
import time
import numpy as np
import zmq

from zmq.tests import BaseZMQTestCase

from online_monitor.utils import utils


def get_test_raw_data(N=20000):
    raw_data = np.array(range(N), dtype=np.uint32)
    data = []
    data.append(raw_data)
    data.extend((float(123.567), float(223.567), int(0)))
    scan_par_id = int(0)
    return data, scan_par_id


def get_test_rec_array_data(N=20000):
    array_data = np.ones((N, ), dtype=[('event_number', '<i8'), ('trigger_number', '<u4')])
    data = []
    data.append(array_data)
    data.extend((float(123.567), float(223.567), int(0)))
    scan_par_id = int(0)
    return data, scan_par_id


def send_normal(socket, data, scan_par_id, name='ReadoutData'):
    data_meta_data = dict(
        name=name,
        dtype=str(data[0].dtype),
        shape=data[0].shape,
        timestamp_start=data[1],  # float
        timestamp_stop=data[2],  # float
        error=data[3],  # int
        scan_par_id=scan_par_id
    )
    socket.send_json(data_meta_data, flags=zmq.SNDMORE | zmq.NOBLOCK)
    socket.send(data[0])  # , flags=zmq.NOBLOCK)


def send_simple(socket, data, scan_par_id, name='ReadoutData'):
    data_meta_data = dict(
        name=name,
        dtype=str(data[0].dtype),
        shape=data[0].shape,
        timestamp_start=data[1],  # float
        timestamp_stop=data[2],  # float
        error=data[3],  # int
        scan_par_id=scan_par_id
    )

    data_ser = utils.simple_enc(data[0], meta=data_meta_data)
    socket.send(data_ser)  # , flags=zmq.NOBLOCK)


def deserialize_normal(socket, data, meta_data=None):
    try:
        meta_data = zmq.utils.jsonapi.loads(data)
        return {'meta_data': meta_data}
    except ValueError:  # Is raw data
        dtype = meta_data.pop('dtype')
        shape = meta_data.pop('shape')
        raw_data = np.frombuffer(data, dtype=dtype).reshape(shape)
        return raw_data


def recv_normal(socket):
    ''' Std. reading and deserialization of our readout systems data '''
    # First message with meta data
    data_rcv = socket.recv()
    data_des = deserialize_normal(socket, data=data_rcv)
    # Second message with raw data
    data_rcv = socket.recv()
    data_des = deserialize_normal(socket, data=data_rcv, meta_data=data_des['meta_data'])
    return data_des


def recv_simple(socket):
    ''' Simple reading and deserialization of our readout systems data '''
    # First message with meta data
    data_rcv = socket.recv()
    array, _ = utils.simple_dec(data_rcv)
    return array


def send_std(socket, data, scan_par_id, name='ReadoutData'):
    data_with_meta_data = dict(
        data=data[0],
        name=name,
        timestamp_start=data[1],  # float
        timestamp_stop=data[2],  # float
        error=data[3],  # int
        scan_par_id=scan_par_id
    )
    data_ser = zmq.utils.jsonapi.dumps(data_with_meta_data, cls=utils.NumpyEncoder)
    socket.send(data_ser)


def recv_std(socket):
    data_ser = socket.recv()
    data_with_meta_data = zmq.utils.jsonapi.loads(data_ser, object_hook=utils.json_numpy_obj_hook)
    return data_with_meta_data['data']


class TestSerialization(BaseZMQTestCase):
    def test_std_send_rcv(self):
        ''' Serialization schema for numpy arrays using json

            https://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays
            Works also with record arrays
        '''
        a, b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        # UInt32 array data
        data, scan_par_id = get_test_raw_data()
        send_std(socket=a, data=data, scan_par_id=scan_par_id, name='testdata')
        A = recv_std(socket=b)
        np.testing.assert_array_equal(data[0], A)
        # Record array data
        data, scan_par_id = get_test_rec_array_data()
        send_std(socket=a, data=data, scan_par_id=scan_par_id, name='testdata')
        A = recv_std(socket=b)
        self.assertTrue((data[0] == A).all())

    def test_normal_send_rcv(self):
        ''' Normal serialization schema for numpy arrays over zeromq

            https://pyzmq.readthedocs.io/en/latest/serialization.html
            Not working for record arrays
         '''
        a, b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        time.sleep(0.5)  # needed to setup socket pair, otherwise first message might be not send
        data, scan_par_id = get_test_raw_data()
        # UInt32 array data
        send_normal(socket=a, data=data, scan_par_id=scan_par_id, name='testdata')
        A = recv_normal(socket=b)
        np.testing.assert_array_equal(data[0], A)
        # Record array data

    def test_simple_send_rcv(self):
        ''' Serialization schema for data with one numpy array only

            Works also with record arrays and is 20% faster than
            https://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays
        '''
        a, b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        # UInt32 array data
        data, scan_par_id = get_test_raw_data()
        send_simple(socket=a, data=data, scan_par_id=scan_par_id, name='testdata')
        A = recv_simple(socket=b)
        np.testing.assert_array_equal(data[0], A)
        # Record array data
        data, scan_par_id = get_test_rec_array_data()
        send_simple(socket=a, data=data, scan_par_id=scan_par_id, name='testdata')
        A = recv_simple(socket=b)
        self.assertTrue((data[0] == A).all())


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSerialization)
    unittest.TextTestRunner(verbosity=2).run(suite)

