# fml

[fantasy movie league](https://fantasymovieleague.com/) prediction as an allocation problem:

Maximize expected revenue subject to finite budget

See [blog post](http://blog.ethanrosenthal.com/2018/08/06/serverless-integer-programming/) for more details

## Installation

```
pip install -r requirements.txt
```

Create a Google Sheet with `inputs` and `outputs` tabs. Create related [OAuth credentials](https://datasheets.readthedocs.io/en/latest/getting_oauth_credentials.html). Download credentials locally and include their names in `conf.yml` file.

## Running locally

You can either run the optimizer script as 

```bash
python -m fml.optimizer
```

or run the Flask app locally

```bash
gunicorn fml.app:app
```

If running the Flask app locally, then replace [this line](https://github.com/EthanRosenthal/fml/blob/master/fml/app/templates/index.html#L11) with 

```html
 <form action="/" method="post">
```

## Deployment


Make a virtual enviornment (using `virtualenv`) with any name that is not `fml`.

Next, use [Zappa](https://github.com/Miserlou/Zappa) to initialize and deploy the app.

```bash
zappa init
zappa deploy dev
```
