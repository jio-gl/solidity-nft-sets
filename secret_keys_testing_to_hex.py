
import json

def getGanacheAccountsHex():
    obj = json.load(open('ganache-accounts.json'))
    outData = []
    count = 0
    for addr in obj['addresses']:
        print ('Address %d: ' % count + addr)
        #print (obj['addresses'][addr])
        # ''.join(map(lambda x : '%x'%x, l))
        l = obj['addresses'][addr]['secretKey']['data']
        secretKey = '0x' + (''.join(map(lambda x : '%.2x'%x, l)))
        print ( 'Secret Key: ' + secretKey )
        l = obj['addresses'][addr]['publicKey']['data']
        publicKey = '0x' + ''.join(map(lambda x : '%x'%x, l))
        print ( 'Public Key: '+ publicKey )
        print (  )
        count += 1
        outData.append( {'address':addr, 'secretKey':secretKey, 'publicKey':publicKey} )
    return outData

json.dump( getGanacheAccountsHex(), open('ganache-accounts-hex.json','w'))

