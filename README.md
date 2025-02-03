# Datenbiene

**Datenbiene** (data bee) is a versatile and powerful data collection tool
designed for multi-modal scientific studies. It facilitates the collection of
data from multiple modalities on different acquisition systems, offering
flexibility and efficiency in managing research data directly after acquisition.


## Features

* Collects data from various sources and modalities / acquisition devices.
* Provides easy configuration through Excel and JSON files.
* Utilizes Jinja2 templates for dynamic placeholders in Excel cells.
* Extensible with custom sources, sinks, and checkers.


## Installation

Ensure you have Python 3 installed. You can install the required packages using
the `requirements.txt` file in a virtual environment:

1. Create a Python virtual environment and activate it:

    ```sh
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

2. Install the dependencies using pip:

    ```sh
    pip install -r requirements.txt
    ```

3. Modify settings and secrets in `config.py` according to your setup.


## Usage

To use Datenbiene, you need to provide an Excel file containing the
configuration for sources, checkers, and sinks, along with an optional JSON file
for key-value pairs.

### Command-line Arguments

* `-e, --excel`: Path to the Excel file containing Sources and Sinks sheets. (required)
* `-j, --json`: Path to the JSON file containing key-value pairs. (required)

### Example

```sh
python datenbiene.py -e sources-sinks.xlsx -j key-vals.json
```


## Configuration

The configuration Excel file should contain the following sheets:

- Sources: Specifies the data sources.
- Checkers: Defines data checkers (to be implemented).
- Sinks: Specifies the data sinks.

The JSON file should contain key-value pairs used for dynamic data processing
with Jinja2 templates applied to all cells in the Excel file.

### Example Excel File

| Name   | Source     | PathPatterns  | FilePatterns | AdditionalOptions |
|--------|------------|---------------|--------------|-------------------|
| Source | SomeSource | /path/to/data | *.csv        | {"option1": "value1"} |

### Example JSON File

```json
{
  "study": "multi-modal-study-01",
  "subject": "ab12",
  "date": 20250202
}
```


## Customization

You can extend Datenbiene by adding custom sources, sinks, and checkers.
Implement your custom classes in the `sources`, `sinks`, and `checkers` modules,
respectively, and update the Excel configuration accordingly.


## License

Datenbiene is licensed under the GPL-3.0-only license. See LICENSE file or
https://www.gnu.org/licenses/gpl-3.0.html for details.


## Authors

Datenbiene is developed by

* Torsten Stöter (torsten.stoeter@lin-magdeburg.de)
* Jörg Stadler
* André Brechmann

all affiliated with Combinatorial NeuroImaging Core Facility at Leibniz
Institute for Neurobiology Magdeburg, Germany.


## Acknowledgements

A special thank you goes to our colleagues Andreas Fügner, Anke Michalsky and
Renate Blobel-Lüer for their continued support in testing and valuable feedback
for improving the Datenbiene software.

