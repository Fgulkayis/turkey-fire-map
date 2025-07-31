import requests
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta 

def home(request):
    return HttpResponse("Harita Projesi Anasayfası!")

def map_view(request):
    return render(request, 'map_app/map.html')

def get_firms_data(request):
    FIRMS_API_KEY = "26874a652f47b5801ec566a68ed179f7" 
    
   
    time_range = request.GET.get('time_range', '24') 
    confidence_filter = request.GET.get('confidence', 'all') 
    daynight_filter = request.GET.get('daynight', 'all') 
    min_frp_filter = request.GET.get('min_frp', '0.0') 


    
    today = datetime.now().date() 
    api_date_param = today.strftime('%Y-%m-%d') 

    if time_range == '24':
        api_date_param = today.strftime('%Y-%m-%d') 
    elif time_range == '48':
        
        two_days_ago = today - timedelta(days=2)
        api_date_param = two_days_ago.strftime('%Y-%m-%d')
    elif time_range == '7':
        seven_days_ago = today - timedelta(days=7)
        api_date_param = seven_days_ago.strftime('%Y-%m-%d')
    elif time_range == '30':
        thirty_days_ago = today - timedelta(days=30)
        api_date_param = thirty_days_ago.strftime('%Y-%m-%d')


    
    firms_url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_API_KEY}/VIIRS_SNPP_NRT/TUR/1/{api_date_param}"

    print(f"FIRMS API URL: {firms_url}")

    try:
        response = requests.get(firms_url)
        response.raise_for_status() 
        
        print(f"API Yanıt Durumu Kodu: {response.status_code}")
        print(f"API Yanıt Metni (İlk 500 karakter): \n{response.text[:500]}")
        
        csv_data = response.text.strip().split('\n')
        
        if len(csv_data) <= 1 or not csv_data[1].strip() or "Error" in csv_data[0] or "Failed" in csv_data[0]:
            print("FIRMS API'den veri gelmedi veya sadece başlık satırı var/hata mesajı döndü.")
            return JsonResponse({
                'fires': [],
                'statistics': {
                    'total_fires': 0,
                    'latest_fire_date': 'Yok',
                    'highest_frp': 'Yok',
                    'most_active_province': 'Yok' 
                }
            })

        headers = [header.strip() for header in csv_data[0].split(',')]
        
        all_fires = []
        for row in csv_data[1:]:
            if not row.strip():
                continue
            values = [val.strip() for val in row.split(',')]
            
            if len(values) != len(headers):
                print(f"Uyarı: Başlık ve değer sayısı uyuşmuyor, satır atlandı: {row}")
                continue
            
            fire_data = dict(zip(headers, values))
            all_fires.append(fire_data)
 
        filtered_fires = []
        for fire in all_fires:
            fire_confidence_api = fire.get('confidence', '').lower()

            if confidence_filter != 'all':
                if confidence_filter == 'low' and fire_confidence_api != 'l':
                    continue
                if confidence_filter == 'nominal' and fire_confidence_api != 'n':
                    continue
                if confidence_filter == 'high' and fire_confidence_api not in ['h', 'e']: 
                    continue
            
            fire_daynight_api = fire.get('daynight', '').upper()
            if daynight_filter != 'all' and fire_daynight_api != daynight_filter:
                continue

            try:
                fire_frp = float(fire.get('frp', '0.0'))
                min_frp_val = float(min_frp_filter)
                if fire_frp < min_frp_val:
                    continue
            except ValueError:
                pass

            filtered_fires.append(fire)

        
        total_fires = len(filtered_fires)
        
        latest_fire_date = 'Yok'
        highest_frp = 0.0
        
        if filtered_fires:
            latest_datetime = None
            
            for fire in filtered_fires:
                try:
                    current_frp = float(fire.get('frp', '0.0'))
                    if current_frp > highest_frp:
                        highest_frp = current_frp

                    acq_date_str = fire.get('acq_date')
                    acq_time_str = fire.get('acq_time')
                    if acq_date_str and acq_time_str:
                        acq_time_padded = acq_time_str.zfill(4) 
                        current_datetime_str = f"{acq_date_str} {acq_time_padded}"
                        current_dt = datetime.strptime(current_datetime_str, '%Y-%m-%d %H%M')
                        
                        if latest_datetime is None or current_dt > latest_datetime:
                            latest_datetime = current_dt

                except (ValueError, TypeError) as e:
                    print(f"Tarih/FRP dönüştürme hatası: {e} for fire: {fire}")
                    continue

            if latest_datetime:
                latest_fire_date = latest_datetime.strftime('%Y-%m-%d %H:%M')
            
            most_active_province = 'Hesaplanmadi' 
        
        statistics = {
            'total_fires': total_fires,
            'latest_fire_date': latest_fire_date,
            'highest_frp': f"{highest_frp:.2f}", 
            'most_active_province': most_active_province
        }

        return JsonResponse({'fires': filtered_fires, 'statistics': statistics})

    except requests.exceptions.RequestException as e:
        print(f"API isteği hatası: {e}")
        return JsonResponse({'error': 'Yangın verileri alınamadı.'}, status=500)
    except Exception as e:
        print(f"Veri işleme hatası: {e}")
        return JsonResponse({'error': 'Veri işlenirken bir hata oluştu.'}, status=500)