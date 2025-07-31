import requests
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

def home(request):
    return HttpResponse("Harita Projesi Anasayfası!")

def map_view(request):
    return render(request, 'map_app/map.html')

def get_firms_data(request):
    FIRMS_API_KEY = "26874a652f47b5801ec566a68ed179f7" 
    

    firms_url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_API_KEY}/VIIRS_SNPP_NRT/TUR/1/2025-07-29" 
    

    
    print(f"FIRMS API URL: {firms_url}")

    try:
        response = requests.get(firms_url)
        response.raise_for_status() 
        
        print(f"API Yanıt Durumu Kodu: {response.status_code}")
        print(f"API Yanıt Metni (İlk 500 karakter): \n{response.text[:500]}")
        
        csv_data = response.text.strip().split('\n')
        
        if len(csv_data) <= 1 or not csv_data[1].strip() or "Error" in csv_data[0] or "Failed" in csv_data[0]:
            print("FIRMS API'den veri gelmedi veya sadece başlık satırı var/hata mesajı döndü.")
            return JsonResponse({'fires': []})

        headers = [header.strip() for header in csv_data[0].split(',')]
        
        fires = []
        for row in csv_data[1:]:
            if not row.strip():
                continue
            values = [val.strip() for val in row.split(',')]
            
            if len(values) != len(headers):
                print(f"Uyarı: Başlık ve değer sayısı uyuşmuyor, satır atlandı: {row}")
                continue
            
            fire_data = dict(zip(headers, values))
            fires.append(fire_data)

        return JsonResponse({'fires': fires})

    except requests.exceptions.RequestException as e:
        print(f"API isteği hatası: {e}")
        return JsonResponse({'error': 'Yangın verileri alınamadı.'}, status=500)
    except Exception as e:
        print(f"Veri işleme hatası: {e}")
        return JsonResponse({'error': 'Veri işlenirken bir hata oluştu.'}, status=500)