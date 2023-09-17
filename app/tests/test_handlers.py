from unittest.mock import patch

from app.core.exception import NodeException


async def test_create_wallet_with_mnemonic(client, wallet_data):
    response = await client.post('/create_wallet', json={'mnemonic': wallet_data['mnemonic']})

    assert response.status_code == 201
    data = response.json()
    assert len(data.keys()) == 5
    assert data.get('address') == wallet_data.get('address')
    assert data.get('private_key') == wallet_data.get('private_key')
    assert data.get('mnemonic') == wallet_data.get('mnemonic')
    assert data.get('leaf') == wallet_data.get('leaf')
    assert data.get('address') in data.get('explorer_url')


async def test_create_wallet_next_leaf(client, wallet):
    response = await client.post('/create_wallet', json={'mnemonic': wallet.mnemonic})

    assert response.status_code == 201
    data = response.json()
    assert len(data.keys()) == 5
    assert data.get('mnemonic') == wallet.mnemonic
    assert data.get('leaf') == wallet.leaf + 1
    assert data.get('address') in data.get('explorer_url')


async def test_create_wallet_without_mnemonic(client):
    response = await client.post('/create_wallet', json={})

    assert response.status_code == 201
    assert len(response.json().keys()) == 5


async def test_wallets_list(client, wallets):
    response = await client.get('/wallets')

    assert response.status_code == 200
    assert len(response.json()) == len(wallets)


async def test_wallets_list_without_pagination(client, wallets):
    response = await client.get('/wallets?limit=1&offset=0')

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_wallet_detail(client, wallet):
    with patch('app.controller.WalletController._get_balance') as provider_mock:
        provider_mock.return_value = 1000000000000000000
        response = await client.get(f'/wallet/{wallet.address}')

        data = response.json()
        assert data['address'] == wallet.address
        assert data['address'] == wallet.address
        assert data['private_key'] == wallet.private_key
        assert data['mnemonic'] == wallet.mnemonic
        assert data['leaf'] == wallet.leaf
        assert data['balance'] == '1.000000000000000000'


async def test_wallet_detail_invalid_address(client):
    response = await client.get('/wallet/123')

    assert response.status_code == 400
    assert 'detail' in response.json()
    assert response.json()['detail'] == 'Address Not Valid'


async def test_wallet_detail_not_found(client):
    response = await client.get('/wallet/0x7e13F900472204F062c270B5E9Cb3CF127B08F18')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Wallet Not Found'


async def test_wallet_detail_not_connected(client, wallet):
    with patch('app.controller.WalletController._get_balance') as provider_mock:
        provider_mock.side_effect = NodeException()
        response = await client.get(f'/wallet/{wallet.address}')

        data = response.json()
        assert response.status_code == 400
        assert data['detail'] == "Node Unavailable"


async def test_wallet_detail_balance_zero(client, wallet):
    with patch('app.controller.WalletController._get_balance') as provider_mock:
        provider_mock.return_value = 1
        response = await client.get(f'/wallet/{wallet.address}')

        data = response.json()
        assert data['address'] == wallet.address
        assert data['address'] == wallet.address
        assert data['private_key'] == wallet.private_key
        assert data['mnemonic'] == wallet.mnemonic
        assert data['leaf'] == wallet.leaf
        assert data['balance'] == '0.000000000000000001'


async def test_send_client_error(client, wallet):
    with patch('app.controller.WalletController._get_balance') as mock_balance:
        mock_balance.side_effect = NodeException()
        response = await client.post(
            f'/wallet/{wallet.address}/send', json={"to": "0xfd267dd115C1e486369D3A5ddF26B8c12f16FdDA", "amount": "1"}
        )

        assert response.status_code == 400
        assert response.json()['detail'] == "Node Unavailable"


async def test_send_invalid_from(client):
    response = await client.post(f'/wallet/123/send', json={"to": "123", "amount": "1"})

    assert response.status_code == 400
    assert response.json()['detail'] == "From Address Not Valid"


async def test_send_invalid_to(client, wallet):
    response = await client.post(f'/wallet/{wallet.address}/send', json={"to": "123", "amount": "1"})

    assert response.status_code == 400
    assert response.json()['detail'] == "To Address Not Valid"


async def test_send_insufficient_funds_fee(client, wallet):
    with patch('app.controller.WalletController._get_balance') as mock_balance:
        mock_balance.return_value = 0
        with patch('app.controller.WalletController._gas_count') as mock_gas_count:
            mock_gas_count.return_value = 1000000000000000000
            with patch('app.controller.WalletController._gas_price') as mock_gas_price:
                mock_gas_price.return_value = 1
                response = await client.post(
                    f'/wallet/{wallet.address}/send',
                    json={'to': "0xfd267dd115C1e486369D3A5ddF26B8c12f16FdDA", "amount": "1"},
                )

                assert response.status_code == 400
                assert response.json()['detail'] == "Insufficient Funds: available 0, required 2"


async def test_send_wallet_not_found(client):
    response = await client.post(
        f'/wallet/0x0af880Ed1dF24Cd35BCA3c9fbD45A5586200e7Cb/send',
        json={"to": '0x0af880Ed1dF24Cd35BCA3c9fbD45A5586200e7Cb', "amount": "1"},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == "Wallet Not Found"


async def test_send_success(client, wallet):
    with patch('app.controller.WalletController._get_balance') as mock_balance:
        mock_balance.return_value = 1000000000000000000
        with patch('app.controller.WalletController._gas_count') as mock_gas_count:
            mock_gas_count.return_value = 0
            with patch('app.controller.WalletController._gas_price') as mock_gas_price:
                mock_gas_price.return_value = 1
                with patch('app.controller.WalletController._send_raw_transaction') as mock_raw_transaction:
                    tx_id = '0xf287c5b4994b6553a0917cd9663bda180524ac7ec0e6639e71288d1e9507cee8'
                    mock_raw_transaction.return_value = tx_id
                    response = await client.post(
                        f'/wallet/{wallet.address}/send',
                        json={'to': "0xfd267dd115C1e486369D3A5ddF26B8c12f16FdDA", "amount": "1"},
                    )

                    assert response.status_code == 200
                    assert response.json()['transaction_id'] == tx_id
                    assert tx_id in response.json()['explorer_url']
