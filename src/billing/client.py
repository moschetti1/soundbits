import requests

class LemonUsageUpdateError(Exception):
    pass

class LemonUsageFetchError(Exception):
    pass

class LemonCustomerFetchError(Exception):
    pass

class Lemon():

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": "Bearer " + self.api_key
        }
        self.base_url = "https://api.lemonsqueezy.com/v1"

    def create_usage_record(self, quantity=1, subscription_item_id="", action="increment"):
        path = "/usage-records"
        endpoint = self.base_url + path
        payload = {
            "data": {
                "type": "usage-records",
                "attributes": {
                    "quantity": quantity,
                    "action": action
                },
                "relationships": {
                    "subscription-item": {
                        "data": {
                            "type": "subscription-items",
                            "id": str(subscription_item_id)
                        }
                    }
                }
            }
        }

        r = requests.post(endpoint, json=payload, headers=self.headers)
        if 200 > r.status_code or r.status_code >= 300:
            raise LemonUsageUpdateError
        return r.json()

    def get_current_usage(self, subscription_item_id):
        path = "/subscription-items/{item_id}/current-usage".format(
            item_id=subscription_item_id
        )
        endpoint = self.base_url + path

        r = requests.get(endpoint, headers=self.headers)
        if 200 > r.status_code or r.status_code >= 300:
            raise LemonUsageFetchError

        return r.json()

    def get_customer_object(self, customer_id):
        path = "/customers/{customer_id}".format(customer_id=customer_id)
        endpoint = self.base_url + path

        r = requests.get(endpoint, headers=self.headers)
        if 200 > r.status_code or r.status_code >= 300:
            raise LemonCustomerFetchError

        return r.json()
