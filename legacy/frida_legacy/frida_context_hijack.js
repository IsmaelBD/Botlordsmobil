var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// Funciones oficiales de red
var fnAddUS = baseAddr.add(0x1D224A0);
var fnAddBY = baseAddr.add(0x1D22860);

var ushort_count = 0;
var byte_count = 0;

// Variables dinámicas (Controladas vía RPC o Memoria)
var target_zone = 507;
var target_point = 59;
var bot_enabled = true;

function dynamicHijack() {
    console.log('[🚀] Lanzando Inyector v14.0 (Control Dinámico Maestro)...');

    Interceptor.attach(fnAddUS, {
        onEnter: function(args) {
            var mp = args[0];
            var proto = mp.add(0x30).readU16();
            
            if (proto === 6615 && bot_enabled) {
                ushort_count++;
                if (ushort_count === 6) {
                    // Aquí el bot secuestra la zona
                    args[1] = ptr(target_zone);
                }
            }
        }
    });

    Interceptor.attach(fnAddBY, {
        onEnter: function(args) {
            var mp = args[0];
            var proto = mp.add(0x30).readU16();
            
            if (proto === 6615 && bot_enabled) {
                byte_count++;
                if (byte_count === 1) {
                    // Aquí el bot secuestra el punto
                    args[1] = ptr(target_point);
                }
            }
        }
    });

    var fnSend = baseAddr.add(0x1D23440);
    Interceptor.attach(fnSend, {
        onEnter: function(args) {
            ushort_count = 0;
            byte_count = 0;
        }
    });

    console.log('[📡] BOT v14.0 EN LÍNEA. Control dinámico activado.');
}

// Exportamos funciones para que Python pueda cambiar las coordenadas
rpc.exports = {
    setcoords: function(zone, point) {
        target_zone = zone;
        target_point = point;
        console.log('[🔄] Bot actualizado a Zona: ' + zone + ', Punto: ' + point);
    },
    setstatus: function(status) {
        bot_enabled = status;
        console.log('[🚦] Bot Estado: ' + (status ? 'ACTIVO' : 'APAGADO'));
    }
};

dynamicHijack();
