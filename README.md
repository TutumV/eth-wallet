# ETH-wallet

## How to start

Edit and copy .example.env 

```
cp .example.env .env
```

Setup database
```
docker-compose up -d postgres
```

Run project in docker

```
docker-compose up -d
```

Run postgres in docker and run application manually

```
pipenv install
uvicorn app.main:app
```

Run tests (if you need specify env file edit .test.env)

```
make test
```

Or Run tests with coverage
```
make coverage
```

You can send HTTP requests from [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
