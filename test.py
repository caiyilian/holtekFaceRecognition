

Str = "http://tomoya.vip3gz.91tunnel.com:80/getTemp/?eqName=001&temp=37.1"

print(Str[Str.find("=")+1:Str.find("&")])
print(Str[Str.rfind("=")+1:])