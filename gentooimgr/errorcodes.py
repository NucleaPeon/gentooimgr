
"""Action performs successfully with no errors
"""
SUCCESS = 0

"""Action has an error due to conditions not being met, such as requiring an --iso, --portage or --stage3
parameter because one could be not be derrived from arguments or configuration.
"""
CONDITIONS_NOT_MET = 1

"""Code is incomplete or cannot be verified as successful due to the current state of development
"""
NOT_IMPLEMENTED = 2

"""Code when a subprocess call fails, stderr at a minimum should be logged when this occurs.
"""
PROCESS_FAILED = 3

"""Code when /mnt/gentoo is not detected and it is assumed you are running in a live environment.
As this is dangerous to do on a configured system, this error is returned; Using the --force option
can bypass this error usually.
"""
NOT_A_GENTOO_LIVE_ENV = 4
