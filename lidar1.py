from rplidar import RPLidar, RPLidarException
#import smbus
import socketio
import eventlet
import json

#bus = smbus.SMBus(1)
#address = 8

#def send_data_to_arduino(data):
#    bus.write_byte(address,data)
#    print("raspberry pi sent: ", data)

lidar = RPLidar('/dev/ttyUSB0')

lidar.__init__('/dev/ttyUSB0', 115200, 5, None)

lidar.connect()

info = lidar.get_info()
print(info)

health = lidar.get_health()
print(health)

# Socket.IO sunucusu oluşturma
sio = socketio.Server()
app = socketio.WSGIApp(sio)

# Bağlantı olayı
@sio.event
def connect(sid, environ, auth):
    print('Client connected:', sid)

# Bağlantı kesilme olayı
@sio.event
def disconnect(sid):
    print('Client disconnected:', sid)

# Her tarama için işleme fonksiyonu
def process_scan(scan_data):
    # Veriyi JSON formatına çevirin
    json_data = json.dumps(scan_data)
    # Veriyi istemcilere gönderin
    sio.emit('lidar_data', json_data)

# Dizi
scan_data = []

try:
    
    for i, scan in enumerate(lidar.iter_scans()):
        
        one_sent = False
        last_angle = None
        
        for d in scan:

            # Degiskenler
            distance = d[2]/10
            angle = d[1]

            scan_data.append({'angle': angle, 'distance': distance})
            
            if 350 <= d[1] <= 360 or 0 <= d[1] <= 10:
                
                if (d[2] / 10) <= 100:
                    one_sent = True
                    print(1)
                    #send_data_to_arduino(1)
                    break
                
                else:
                    one_sent = False
                    
            if last_angle is not None and abs((last_angle - d[1]) % 360) > 355:

                # Her bir tarama verisi işlendiğinde, işlenmiş veriyi gönder
                process_scan(scan_data)

                # Dizi Sifirla
                scan_data = []

                one_sent = False
            
            last_angle = d[1]
            
        if not one_sent:
            print(0)
            #send_data_to_arduino(0)
            one_sent = False
        
except KeyboardInterrupt as err:
    print('key board interupt')
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()

except RPLidarException as err:
    print(err)
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()
    
except AttributeError:
    print('hi attribute error')

if __name__ == '__main__':
    # Eventlet ile Socket.IO sunucusunu çalıştır
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)