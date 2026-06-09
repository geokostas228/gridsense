db = db.getSiblingDB("gridsense_catalog");

db.equipment.insertMany([
  {
    equipment_id: "TX-1001",
    type: "Transformer",
    manufacturer: "Siemens",
    installation_date: "2021-05-12",
    district: "North",
    specifications: {
      capacity_kva: 500,
      voltage_primary: 20000,
      voltage_secondary: 400
    },
    maintenance_history: [
      {
        date: "2024-02-10",
        technician: "Kostas Nikolaou",
        notes: "Oil replacement completed"
      },
      {
        date: "2025-01-15",
        technician: "Maria Ioannou",
        notes: "Thermal inspection passed"
      }
    ]
  },
  {
    equipment_id: "SM-2045",
    type: "SmartMeter",
    manufacturer: "Landis+Gyr",
    installation_date: "2023-08-03",
    district: "Central",
    firmware: {
      version: "2.4.1",
      last_update: "2026-03-01"
    },
    connectivity: {
      protocol: "LoRaWAN",
      signal_strength: -71
    }
  }
]);