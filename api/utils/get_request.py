

def get_request_data(request):
    if request.files and "file" in request.files:
       file= request.files["file"]
       extra= request.form.get("extra", "")
       return file, extra or ""
    elif request.is_json:
        data= request.get_json()
        extra= data.get("extra", "") if data else ""
        return data, (extra or "")
    else:
        return None, None

