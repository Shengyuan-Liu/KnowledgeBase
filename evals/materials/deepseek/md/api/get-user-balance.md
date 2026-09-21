# Get User Balance

Source: https://api-docs.deepseek.com/api/get-user-balance
Captured: 2026-09-21T19:37:05.988Z

```
GET /user/balance
```

Get user current balance

## Responses

OK, returns user balance info.

**Schema**

**is\_available** boolean

Whether the user's balance is sufficient for API calls.

**balance\_infos**

object\[\]

-   Array \[

**currency** string

**Possible values:** \[`CNY`, `USD`\]

The currency of the balance.

**total\_balance** string

The total available balance, including the granted balance and the topped-up balance.

**granted\_balance** string

The total not expired granted balance.

**topped\_up\_balance** string

The total topped-up balance.

-   \]

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "110.00",
      "granted_balance": "10.00",
      "topped_up_balance": "100.00"
    }
  ]
}
```

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "110.00",
      "granted_balance": "10.00",
      "topped_up_balance": "100.00"
    }
  ]
}
```
