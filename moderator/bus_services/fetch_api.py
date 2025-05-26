import requests

# /ShuttleService
# params: busstopname
# response.json()["ShuttleServiceResult"]["shuttles"]: list of services
# "name": Name of bus service, "_etas": list of buses
# Each bus: dictionary with keys "plate", "eta"


if __name__ == "__main__":
    base_url = "https://nnextbus.nusmods.com/arrival"
    url = f"{base_url}"
    response = requests.get(url=url)
    print(response.json())

