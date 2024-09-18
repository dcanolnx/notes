const mysql = require('mysql');
const pool = mysql.createPool({
  connectionLimit: 10,
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME
});

exports.handler = async (event) => {
  const data = JSON.parse(event.body);

  return new Promise((resolve, reject) => {
    const values = [
      [
        data.hostname,
        data.uptime_system,
        data.uptime_system_minutes,
        data.status_eea, data.uptime_eea,
        data.status_eraagent, data.uptime_eraagent,
        data.status_wazuh, data.uptime_wazuh,
        data.date_collected
      ]
    ];

    pool.query('INSERT INTO compliance_info (hostname, uptime_system, uptime_system_minutes, status_eea, uptime_eea, status_eraagent, uptime_eraagent, status_wazuh, uptime_wazuh, date_collected) VALUES ?', [values], (error, results) => {
      if (error) {
        reject(new Error(error));
      } else {
        resolve({
          statusCode: 200,
          body: JSON.stringify({ message: 'Data inserted successfully.' })
        });
      }
    });
  });
};
