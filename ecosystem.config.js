const path = require("path");
const fs = require("fs");

// Base directory
const base = path.resolve(__dirname);

// Helper to check if hotkey exists
const hotkeyExists = (walletName, hotkeyName) => {
  const hotkeyPath = path.join(process.env.HOME, ".bittensor", "wallets", walletName, "hotkeys", hotkeyName);
  return fs.existsSync(hotkeyPath);
};

// Base configuration for all apps
const baseConfig = {
  interpreter: path.join(base, ".venv", "bin", "python3"),
  cwd: base,
  error_file: path.join(base, "logs"),
  out_file: path.join(base, "logs"),
  log_date_format: "YYYY-MM-DD HH:mm:ss",
  max_restarts: 10,
  min_uptime: "10s",
  restart_delay: 4000,
  autorestart: true,
  watch: false
};

// Base environment variables
const baseEnv = {
  NETWORK: process.env.NETWORK || "finney",
  SUBNET_UID: process.env.SUBNET_UID || "90",
  API_URL: process.env.API_URL || "https://api.subnet90.com",
  LOG_LEVEL: process.env.LOG_LEVEL || "INFO",
  LOG_FORMAT: process.env.LOG_FORMAT || "json",
  LOG_DIR: "./logs",
  MAX_WORKERS: process.env.MAX_WORKERS || "4",
  REQUEST_TIMEOUT: process.env.REQUEST_TIMEOUT || "30",
  WALLET_NAME: process.env.WALLET_NAME || "my_wallet"
};

// Configuration for miners
const minerConfigs = [
  { name: "miner1", port: "8091", hotkey: "miner1" },
  { name: "miner2", port: "8092", hotkey: "miner2" },
  { name: "miner3", port: "8093", hotkey: "miner3" }
];

// Configuration for validators
const validatorConfigs = [
  { name: "validator1", port: "9091", hotkey: "validator" }
];

// Generate app configurations
const apps = [];

// Add miners if their hotkeys exist
minerConfigs.forEach(config => {
  if (hotkeyExists(baseEnv.WALLET_NAME, config.hotkey)) {
    apps.push({
      ...baseConfig,
      name: config.name,
      script: path.join(base, "run_miner.py"),
      error_file: path.join(base, "logs", `${config.name}.error.log`),
      out_file: path.join(base, "logs", `${config.name}.log`),
      env: {
        ...baseEnv,
        HOTKEY_NAME: config.hotkey,
        MINER_PORT: config.port,
        MINER_STRATEGY: process.env.MINER_STRATEGY || "hybrid",
        MINER_ID: config.name,
        STRATEGY_WEIGHTS: process.env.STRATEGY_WEIGHTS || '{"ai": 0.6, "heuristic": 0.4}'
      }
    });
  }
});

// Add validators if their hotkeys exist
validatorConfigs.forEach(config => {
  if (hotkeyExists(baseEnv.WALLET_NAME, config.hotkey)) {
    apps.push({
      ...baseConfig,
      name: config.name,
      script: path.join(base, "run_validator.py"),
      error_file: path.join(base, "logs", `${config.name}.error.log`),
      out_file: path.join(base, "logs", `${config.name}.log`),
      env: {
        ...baseEnv,
        HOTKEY_NAME: config.hotkey,
        VALIDATOR_PORT: config.port
      }
    });
  }
});

// Show status message
if (apps.length === 0) {
  console.log("\n⚠️  WARNING: No hotkeys found!");
  console.log(`Searched in: ${path.join(process.env.HOME, ".bittensor", "wallets", baseEnv.WALLET_NAME, "hotkeys")}`);
  console.log("\nTo create hotkeys, run:");
  console.log(`  btcli wallet new_hotkey --wallet.name ${baseEnv.WALLET_NAME} --wallet.hotkey miner1`);
  console.log("\nMiners and validators will not start until their hotkeys have been created.\n");
} else {
  console.log(`\n✅ Found ${apps.length} hotkey(s), configuring: ${apps.map(a => a.name).join(", ")}\n`);
}

module.exports = { apps };