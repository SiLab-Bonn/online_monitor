from pkg_resources import get_distribution
from online_monitor.utils.settings import check_package_initialized

# http://stackoverflow.com/questions/17583443/what-is-the-correct-way-to-share-package-version-with-setup-py-and-the-package
__version__ = get_distribution('online_monitor').version

# Initialize online monitor default plugins and example paths
check_package_initialized()
