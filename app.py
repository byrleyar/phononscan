# https://ayumitanaka13.medium.com/how-to-use-ajax-with-python-flask-729c0a8e5346

from flask import Flask, request, render_template
import requests
import json
import os
import sys
from dotenv import load_dotenv
from web3 import Web3
from ens import ENS
import re
from ratelimit import limits, RateLimitException, sleep_and_retry # https://akshayranganath.github.io/Rate-Limiting-With-Python/
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
etherscan_endpoint_url = "https://api-rinkeby.etherscan.io/api"
infura_url = "https://mainnet.infura.io/v3/" + os.getenv('INFURA_PROJECT_ID')
startblock = "0"
endblock = "99999999"
WALLET_SCAN_MAX_TX = 25

web3 = Web3(Web3.HTTPProvider(infura_url))
ns = ENS.fromWeb3(web3)

@sleep_and_retry
@limits(calls=4, period=1)
def rate_limited_etherscan_call(etherscan_endpoint_url, parameters):
    response = requests.get(etherscan_endpoint_url, params=parameters)
    return response

#app = Flask(__name__)

#@app.route("/")
#def index2():
#    return render_template('index2.html')

#background process happening without any refreshing
#@app.route('/process')
#def background_process_test():
#    print ("Hello")
#    return ("nothing")

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    @app.route('/', methods=['GET','POST'])
    def index():
        if request.method == "POST": # POST
            #print("in post")
            text = request.form['rinput']
            rinput = text.lower()
            print(rinput)
            output = {
                'message': '',
                'data': '',
                'most recent transactions': ''
            }
            inputstatus = checkInput(rinput)
            
            if inputstatus == 0:
                print("Invalid input. Please try again")
                output['data'] = "Invalid input"
                output['message'] = "Please try again"
                output.pop('most recenttransactions', None)
                return output
            elif inputstatus == 1: # ENS
                print("ENS found")
                address = ns.address(rinput)
                if str(address) == "None":
                    #print("not an ENS")
                    output['message'] = rinput + " is not a valid ENS"
                    output.pop('most recent transactions', None)
                    return output

                wallet_check = isWalletAPhonon(address)
                num_of_transactions = len(wallet_check['result'])
                output['data'] = {'address':wallet_check['address']}
                #dnsearch = ns.name(address)
                #if dnsearch == "None":
                #    this_wallet = rinput
                #else:
                #    this_wallet = dnsearch
                if num_of_transactions == 1:
                    #created_by = response.json()['result'][0]['from']
                    created_by = str(ns.name(wallet_check['result'][0]['from']))
                    print("This wallet might be an existing phonon created by " + created_by + ".")
                    output['message'] = rinput + " might be an existing phonon created by " + created_by + "."
                    #jprint(output)
                elif num_of_transactions == 2:
                    #created_by = response.json()['result'][1]['from']
                    #redeemed_by = response.json()['result'][0]['to']
                    created_by = wallet_check['result'][1]['from']
                    redeemed_by = wallet_check['result'][0]['to']
                    print("This wallet might be a redeemed phonon that was created by " + created_by + " and redeemed by " + redeemed_by + ".")
                    output['message'] = rinput + " might be a redeemed phonon that was created by " + created_by + " and redeemed by " + redeemed_by + "."
                else:
                    #print("wallet has " + str(len(response.json()['result'])) + " transactions. Probably not a phonon.")
                    print(rinput + " has " + str(num_of_transactions) + " transactions. Probably not a phonon.")
                    output['message'] = rinput + " is probably not a phonon"
                    output['most recent transactions'] = stepThroughWallet(wallet_check)
                #jprint(output)
                if output['most recent transactions'] == '':
                    output.pop('most recenttransactions', None)
                
                
                return output
            elif inputstatus == 2:  # wallet

                wallet_check = isWalletAPhonon(rinput)
                #jprint(wallet_check)
                output['data'] = {'address':wallet_check['address']}
                dnsearch = str(ns.name(rinput))
                #print(dnsearch)
                if dnsearch == "None":
                    this_wallet = rinput
                    #print("dnsearch = none")
                else:
                    this_wallet = dnsearch
                    #print("dnsearch = dns")
                print("this wallet: " + this_wallet)
                num_of_transactions = len(wallet_check['result'])
                if num_of_transactions == 1:
                    #created_by = response.json()['result'][0]['from']
                    #created_by = wallet_check['result'][0]['from']
                    dnsearch = str(ns.name(wallet_check['result'][0]['from']))
                    if dnsearch == "None":
                        created_by = wallet_check['result'][0]['from']
                    else:
                        created_by = dnsearch
                    print("this wallet might be an existing phonon created by " + created_by + ".")
                    #output['data'] = {'address':wallet_check['result'][0]['from']}
                    output['message'] = this_wallet + " might be an existing phonon created by " + created_by
                elif num_of_transactions == 2:
                    #created_by = wallet_check['result'][1]['from']
                    redeemed_by = wallet_check['result'][0]['to']
                    dnsearch = str(ns.name(wallet_check['result'][1]['from']))
                    if dnsearch == "None":
                        created_by = wallet_check['result'][1]['from']
                    else:
                        created_by = dnsearch
                    
                    dnsearch = str(ns.name(wallet_check['result'][0]['to']))
                    if dnsearch == "None":
                        redeemed_by = wallet_check['result'][0]['to']
                    else:
                        redeemed_by = dnsearch
                    
                    print("This wallet might be a redeemed phonon that was created by " + created_by + " and redeemed by " + redeemed_by + ".")
                    output['message'] = this_wallet + " might be a redeemed phonon that was created by " + created_by + " and redeemed by " + redeemed_by
                    
                else:
                    #print("wallet has " + str(len(response.json()['result'])) + " transactions. Probably not a phonon.")
                    print("wallet has " + str(num_of_transactions) + " transactions. Probably not a phonon.")
                    output['message'] = this_wallet + " is probably not a phonon"
                    output['most recent transactions'] = stepThroughWallet(wallet_check)    
                
                if output['most recent transactions'] == '':
                    output.pop('most recent transactions', None)
                
                return output
            
            elif inputstatus == 3: # contract
                print("This is a contract address. We don't support those yet.")
                output['message'] = "This is a contract address. We don't support those yet."
                output.pop('most recent transactions', None)
                return output
                
            elif inputstatus == 4: # transaction hash
                print("transaction hash found") 
                output['message'] = "This is a transaction hash.  We don't support those yet."
                output.pop('most recent transactions', None)
                return output
        
        return render_template('index.html')
    return app

def checkInput(inputstring):
    if inputstring[-4:] == ".eth":
        # might be an ENS name 
        #print("might be an ENS name")
        return 1 # ENS
    elif len(inputstring) == 42 and inputstring[0] == "0" and inputstring[1] == "x":
        # might be wallet or contract address
        #print("might be wallet or contract address")
        if is_wallet_valid(inputstring):
            test_input = web3.eth.get_code(web3.toChecksumAddress(inputstring)).hex()
            if test_input == "0x":
                #print(inputstring + " is a wallet")
                return 2 # wallet
            else:
                #print(inputstring + " is a contract")
                return 3 # contract
        else:
            #print(inputstring + " is not a valid hex string")
            return 0 # not valid hex
    elif len(inputstring) == 66 and inputstring[0] == "0" and inputstring[1] == "x":
        # might be a transaction hash
        #print("might be a transaction hash")
        if is_transaction_valid(inputstring):
            #print(inputstring + " is a valid transaction")
            return 4  # transaction hash
        else:
            #print(inputstring + " is not a valid transaction") 
            return 0 # not valid hex
    else:
        #print("didn't understand the input")
        return 0 # not valid hex or ENS
    
    
def isWalletAPhonon(rawaddress):
    # determine if a wallet could be a phonon
    # make the input all lower case 
    address = rawaddress.lower()

    parameters = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": startblock,
        "endblock": endblock,
        #"page": 1,
        #"offset": 10,
        "sort": "desc",
        "apikey": etherscan_api_key
    }
    
    response = rate_limited_etherscan_call(etherscan_endpoint_url, parameters)
    response_json = response.json()
    
    if response_json['message'] == "OK":
        # response from etherscan was good
        # add address to the results for later use
        response_json['address'] = address

        return response_json
    elif response_json['message'] == "NOTOK":
        jprint(response_json)
        print("message from etherscan: " + response['result'])
        return response_json
    else:
        print("====something went wrong in isWalletAPhonon()====")
        jprint(response_json)
        return 0    

def is_transaction_valid(tx_hash) -> bool:
    pattern = re.compile(r"^0x[a-fA-F0-9]{64}")
    return bool(re.fullmatch(pattern, tx_hash))

def is_wallet_valid(wallet_hash) -> bool:
    pattern = re.compile(r"^0x[a-fA-F0-9]{40}")
    return bool(re.fullmatch(pattern, wallet_hash))

def stepThroughWallet(wallet_data):
    if len(wallet_data['result']) > WALLET_SCAN_MAX_TX:
        print("Stepping through the " + str(WALLET_SCAN_MAX_TX) + " recent transactions from " + str(wallet_data['address']) + " to see if it interacted with phonons.")
    else:
        #print("Stepping through transactions from " + address + " to see if it interacted with phonons.")
        print("Stepping through transactions from " + str(wallet_data['address']) + " to see if it interacted with phonons.")
    
    
    dnsearch = str(ns.name(wallet_data['address']))
    #print(dnsearch)
    if dnsearch == "None":
        this_wallet = wallet_data['address']
        print("dnsearch = none")
    else:
        this_wallet = dnsearch
    
    y = 0
    keys = []
    values = []
    for x in wallet_data['result']:
        #print(x['from'])
        # example 2: key/value https://tutorial.eyehunts.com/python/python-create-a-dictionary-in-the-loop-example-code/
        #keys = []
        #values = []
        y = y + 1
        keys.append(y)
        if y == WALLET_SCAN_MAX_TX: break
        if x['from'] == wallet_data['address']:
            #keys[y-1] = "TX " + str(y-1)
            new_wallet_check = isWalletAPhonon(x['to'])
            #jprint(new_wallet_check)
            if len(new_wallet_check['result']) == 1:
                # wallet might have created a phonon that still exists
                #print("TX " + str(y) + ": " + address + " might have created a phonon that still exists (" + new_address + ")")
                print("TX " + str(y) + ": " + str(wallet_data['address']) + " might have created a phonon that still exists (" + str(x['to']) + ")")
                values.append(str(this_wallet) + " might have created a phonon that still exists (" + str(x['to']) + ")")
            elif len(new_wallet_check['result']) == 2:
                # wallet might have created a phonon that has since been redeemed
                #print("TX " + str(y) + ": " + address + " might have created a phonon that has since been redeemed (" + new_address + ")")
                raw_redeemed_by = new_wallet_check['result'][0]['to']
                dnsearch = str(ns.name(raw_redeemed_by))
                if dnsearch == "None":
                    redeemed_by = raw_redeemed_by
                else:
                    redeemed_by = dnsearch
                print("TX " + str(y) + ": " + str(wallet_data['address']) + " might have created a phonon that has since been redeemed (" + str(x['to']) + ")")
                values.append(str(this_wallet) + " might have created a phonon that has since been redeemed by " + str(redeemed_by) + " (" + str(x['to']) + ")")
            else:
                # wallet sent to another multi-tx wallet -- probably not a phonon
                print("TX " + str(y) + ": not a phonon transaction")
                values.append("not a phonon transaction")
            
        elif x['to'] == wallet_data['address']:
            #keys[y-1] = "TX " + str(y-1)
            new_wallet_check = isWalletAPhonon(x['from'])
            #jprint(new_wallet_check)
            if len(new_wallet_check['result']) == 1:
                # it should never happen that a wallet received ETH from an address that only has 1 transaction
                print("TX " + str(y) + ": investigate this -- this shouldn't happen")
                values.append("investigate this -- this shouldn't happen")
            elif len(new_wallet_check['result']) == 2:
                # wallet might have created a phonon that has since been redeemed
                #print("TX " + str(y) + ": " + address + " might have redeemed a phonon (" + new_address + ")")
                print("TX " + str(y) + ": " + str(wallet_data['address']) + " might have redeemed a phonon (" + str(x['from']) + ")")
                values.append(str(this_wallet) + " might have redeemed a phonon (" + str(x['from']) + ")")
            else:
                # wallet sent to another multi-tx wallet -- probably not a phonon
                print("TX " + str(y) + ": not a phonon transaction")
                values.append("not a phonon transaction")
            #else: 
            #    #error
            #    return
        else:
            print("huh. i'm not sure what this transaction is")
            #keys[y-1] = "TX " + str(y-1)
            values.append("huh. i'm not sure what this transaction is")
    #print(keys)
    #print(values)
    #return tx_list
    tx_list = {}
    for i in range(len(values)):
        tx_list[keys[i]] = values[i]
    #print(tx_list)
    return tx_list


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)



