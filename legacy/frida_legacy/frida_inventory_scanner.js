var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVA DataManager.get_Instance: 0xD458C0
var fnGetInstance = new NativeFunction(baseAddr.add(0xD458C0), 'pointer', []);

function scanInventory() {
    var dm = fnGetInstance();
    if (dm.isNull()) return "DataManager no listo";
    
    // CurHeroID está en 0x6E0 (según dump clásico)
    var curHero = dm.add(0x6E0).readU16();
    
    // Troops (Soldier array) está en 0x4B0. Es un uint[16]
    var troops = [];
    var troopPtr = dm.add(0x4B0).readPointer();
    if (!troopPtr.isNull()) {
        for (var i = 0; i < 16; i++) {
            troops.push(troopPtr.add(0x20 + (i * 4)).readU32());
        }
    }
    
    return { hero: curHero, troops: troops };
}

console.log(JSON.stringify(scanInventory()));
