"""utils package initializer.

Automatically load environment variables from a `.env` file when the
`python-dotenv` package is available. This ensures all modules under
`utils` see values from the user's `.env` without each module calling
`load_dotenv()` individually.
"""

try:
	from dotenv import load_dotenv
	load_dotenv()
except ImportError:
	# If python-dotenv is not installed, silently continue; callers
	# can still read from the real environment.
	pass
