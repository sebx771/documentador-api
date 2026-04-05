

def get_request_data(request):
    if request.files:
       file= request.files["file"]
       extra= request.form.get("extra", "")
       return file, extra
    elif request.json:
        data= request.get_json()
        extra= data.get("extra", "")
        return data, extra
    else:
        return None, None

