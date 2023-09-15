from unittest.mock import patch


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


async def test_create_wallet_next_leaf(client, wallets):
    wallet = wallets[0]
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


async def test_wallet_detail(client, wallets):
    wallet = wallets[0]
    with patch('app.controller.WalletController._get_balance') as provider_mock:
        provider_mock.return_value = 1000000000000000000
        response = await client.get(f'/wallet/{wallet.address}')

        data = response.json()
        assert data['address'] == wallet.address
        assert data['address'] == wallet.address
        assert data['private_key'] == wallet.private_key
        assert data['mnemonic'] == wallet.mnemonic
        assert data['leaf'] == wallet.leaf
        assert data['balance'] == '1'


async def test_wallet_detail_invalid_address(client):
    response = await client.get('/wallet/123')

    assert response.status_code == 400
    assert 'detail' in response.json()
    assert response.json()['detail'] == 'Address Not Valid'


async def test_wallet_detail_not_found(client):
    response = await client.get('/wallet/0x7e13F900472204F062c270B5E9Cb3CF127B08F18')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Wallet Not Found'


async def test_wallet_detail_not_connected(client, wallets):
    wallet = wallets[0]
    with patch('app.controller.WalletController._get_balance') as provider_mock:
        provider_mock.return_value = None
        response = await client.get(f'/wallet/{wallet.address}')

        data = response.json()
        assert data['address'] == wallet.address
        assert data['private_key'] == wallet.private_key
        assert data['mnemonic'] == wallet.mnemonic
        assert data['leaf'] == wallet.leaf
        assert data['balance'] is None


async def test_wallet_detail_balance_zero(client, wallets):
    wallet = wallets[0]
    with patch('app.controller.WalletController._get_balance') as provider_mock:
        provider_mock.return_value = 0
        response = await client.get(f'/wallet/{wallet.address}')

        data = response.json()
        assert data['address'] == wallet.address
        assert data['address'] == wallet.address
        assert data['private_key'] == wallet.private_key
        assert data['mnemonic'] == wallet.mnemonic
        assert data['leaf'] == wallet.leaf
        assert data['balance'] == '0'
