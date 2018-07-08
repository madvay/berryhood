## Usage
````
usage: monlog.py [-h] [-s] [--sensehat_required] [-i]
                 [--ifttt_period IFTTT_PERIOD] [-p PERIOD]
                 [--min_temp MIN_TEMP] [--max_temp MAX_TEMP]
                 [--min_freq MIN_FREQ] [--max_freq MAX_FREQ]
                 [--led_rotation LED_ROTATION] [--log LOG]
                 [--log_days LOG_DAYS] [--log_period LOG_PERIOD]

Monitor Logger

optional arguments:
  -h, --help            show this help message and exit
  -s, --sensehat        enables the Sense HAT LEDs, optionally (default:
                        False)
  --sensehat_required   fails if the Sense HAT LED cannot be loaded (requires
                        --sensehat also) (default: False)
  -i, --ifttt           posts metrics to IFTTT using the key stored in env var
                        IFTTT_TOKEN (default: False)
  --ifttt_period IFTTT_PERIOD
                        send an IFTTT post every N executions (default: 1)
  -p PERIOD, --period PERIOD
                        seconds to sleep between monitoring (default: 1)
  --min_temp MIN_TEMP   Min bar graph temperature (default: 40)
  --max_temp MAX_TEMP   Max bar graph temperature (default: 80)
  --min_freq MIN_FREQ   Min bar graph frequency (default: 600000000)
  --max_freq MAX_FREQ   Max bar graph frequency (default: 1400000000)
  --led_rotation LED_ROTATION
                        rotation of the Sense HAT LEDs (90deg increments)
                        (default: 0)
  --log LOG             path to log to (default: None)
  --log_days LOG_DAYS   days of logs to keep (default: 7)
  --log_period LOG_PERIOD
                        print/log every N executions (default: 1)
````

## Sense HAT display

<img src="https://raw.githubusercontent.com/madvay/berryhood-diagrams/master/monlog/monlog.svg?sanitize=true" />

Includes:

* (a) Alternate blinking light to indicate monlog is running.  Also provides a reference point for the bottom-right and orientation.
* (b) Bar graph of SoC temperature (default: 40C to 80C)
* (c) Bar graph of arm core frequency (default: 600MHz to 1400MHz)
* (d) Current throttling status: bottom/red - undervoltage; middle/green - frequency capped; blue/top - throttled  
* (e) Past throttling status (see (d) for colors)

## Running as a daemon



## License
See [LICENSE](../LICENSE).
