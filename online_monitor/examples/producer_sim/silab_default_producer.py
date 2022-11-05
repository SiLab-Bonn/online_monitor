import time
import tables as tb
import zmq

from online_monitor.utils.producer_sim import ProducerSim
from online_monitor.utils import utils 


class SiLabDefaultProducerSim(ProducerSim):
    """
    Producer simulator reading standard SiLab DAQ system HDF5 data and replying it
    """

    def setup_producer_device(self):
        self.producer_delay = self.config.get('delay', 0.1)  # Delay in seconds
        return super(SiLabDefaultProducerSim, self).setup_producer_device()

    def pack_and_enc(self, data, meta, scan_params=None, name=''):

        # Generate meta data dict from numpy structured array
        meta_data = {}

        for key in meta.dtype.names:
            # Convert numpy dtype to native Python using e.g. np.int64.item()-method if possible
            try:
                meta_data[key] = meta[key].item()
            except AttributeError:
                meta_data[key] = meta[key]

            if "error" in key:
                meta_data['readout_error'] = meta_data[key]    
            

        # Add desscriptor of data dtype
        meta_data['name'] = self.kind if name == '' else name
        meta_data['dtype'] = str(data.dtype)    
        meta_data['scan_parameters'] = {} if scan_params is None else scan_params

        # Encode and return
        return utils.simple_enc(data=data, meta=meta_data)

    def send_data(self):

        for raw_data, meta_data, scan_params in self._get_chunks():

            try:
                ser = self.pack_and_enc(data=raw_data, meta=meta_data, scan_params=scan_params)
                self.sender.send(ser, flags=zmq.NOBLOCK)  # PyZMQ supports sending numpy arrays without copying any data
            except zmq.Again:
                pass
            
            time.sleep(self.producer_delay)
    
    def _get_chunks(self):
        
        with tb.open_file(self.config['data_file'], mode='r') as data_file:

            required_nodes = ('raw_data', 'meta_data')
            missing_nodes = [r for r in required_nodes if r not in data_file.root]
            if missing_nodes:
                raise RuntimeError(f"Some root nodes are required but not present in {self.config['data_file']}: {', '.join(missing_nodes)} missing!")

            # Extract meta data and determine number of readouts
            meta_data = data_file.root.meta_data[:]
            n_readouts = len(meta_data)
            
            # Get data handle
            raw_data = data_file.root.raw_data    
            
            # Optional scan params
            try:
                scan_params = data_file.root.scan_parameters
                scan_param_names = scan_params.dtype.names
            except tb.NoSuchNodeError:
                scan_params = None
                
            self.last_readout_time = time.time()

            for i in range(n_readouts):

                # This readouts meta data    
                meta = meta_data[i]

                # Raw data indeces of readout
                i_start = meta['index_start']
                i_stop = meta['index_stop']

                # get current slice of data
                raw = raw_data[i_start:i_stop]

                # Time stamp of readout
                t_start = meta['timestamp_start']

                # Make a chunk
                if scan_params is not None:
                    chunk = (raw, meta,  {str(scan_param_names): scan_params[i]})
                else:
                    chunk = (raw, meta, {})   

                # Replay timings
                # Determine replay delays
                if i == 0:  # Initialize on first readout
                    self.last_timestamp_start = t_start
                now = time.time()
                delay = now - self.last_readout_time
                additional_delay = t_start - self.last_timestamp_start - delay
                if additional_delay > 0:
                    # Wait if send too fast, especially needed when readout was
                    # stopped during data taking (e.g. for mask shifting)
                    time.sleep(additional_delay)
                self.last_readout_time = time.time()
                self.last_timestamp_start = t_start

                yield chunk
