from urllib import request, parse


mypath = f"""E:\Tanweer Internships & Jobs\DSA\CP"""
exe_command = {"mykey": f"""cd "{mypath}" && ls -l"""}
data = parse.urlencode(exe_command).encode("utf-8")
req = request.Request("http://localhost:8000/", data=data)
with request.urlopen(req, data=data) as f:
    resp = f.read().decode("utf-8")
    print(resp)
