// Inicialización MongoDB Contingencia
db = db.getSiblingDB('contingencia_coop');

db.createCollection('transacciones_respaldo');
db.createCollection('eventos_failover');
db.createCollection('metadata_sync');

db.transacciones_respaldo.createIndex({ "transaccion_id": 1 }, { unique: true });
db.transacciones_respaldo.createIndex({ "fecha_operacion": -1 });
db.eventos_failover.createIndex({ "fecha": -1 });

db.metadata_sync.insertOne({
    descripcion: "Contingencia Cooperativa Financiera PC3",
    origen: "SRV-CoreBancario",
    protocolo: "sync_script_periodico",
    red: "net_contingencia (Zero Trust - internal)",
    puerto: 27017,
    fecha_inicializacion: new Date()
});

print("MongoDB contingencia_coop inicializado.");
