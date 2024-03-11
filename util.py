import base64, email.utils, hmac, hashlib, urllib

def sign(method, host, path, params, skey, ikey):
    """
    Return HTTP Basic Authentication ("Authorization" and "Date") headers.
    method, host, path: strings from request
    params: dict of request parameters
    skey: secret key
    ikey: integration key
    """
    
    # create canonical string
    now = email.utils.formatdate()
    canon = [now, method.upper(), host.lower(), path]
    args = []
    if params!={}:
        for key in sorted(params.keys()):
            val = params[key].encode("utf-8")
            args.append(
                '%s=%s' % (urllib.parse.
                        quote(key, '~'), urllib.parse.quote(val, '~')))
    canon.append('&'.join(args))
    canon = '\n'.join(canon)
    
    # sign canonical string
    sig = hmac.new(bytes(skey, encoding='utf-8'),
                   bytes(canon, encoding='utf-8'),
                   hashlib.sha1)
    auth = '%s:%s' % (ikey, sig.hexdigest())

    # return headers
    return {'Date': now, 'Authorization': 'Basic %s' % base64.b64encode(bytes(auth, encoding="utf-8")).decode()}

