const web3 = require("@solana/web3.js");

// 配置 WebSocket 端点（请替换为你的 Solana RPC WebSocket 端点）
const WSS_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=52eedaeb-aef0-4cc5-94a9-f4cdf8b9fb97"; // 替换为你的 WSS 端点
const PUMP_FUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"; // pump.fun 程序 ID

// 创建 WebSocket 连接
const connection = new web3.Connection(WSS_ENDPOINT, {
  wsEndpoint: WSS_ENDPOINT,
  commitment: "confirmed",
});

// 异步函数：订阅日志并监听 Create 指令
async function subscribeToPumpFunLogs() {
  try {
    // 订阅 pump.fun 程序的日志
    const subscriptionId = connection.onLogs(
      new web3.PublicKey(PUMP_FUN_PROGRAM_ID),
      (logs) => {
        // 检查日志中是否包含 "Program log: Instruction: Create"
        if (logs.logs.join('').includes('Create')) {
          console.log("检测到 pump.fun 创建交易:");
          console.log("交易签名:", logs.signature);
          console.log("日志:", logs.logs);
          console.log("----------------------------------------");
        console.log(logs)
        }
        // console.log(logs)
      },
      "confirmed"
    );

    console.log("已订阅 pump.fun 日志，订阅 ID:", subscriptionId);

    // 保持脚本运行以持续监听
    process.on("SIGINT", async () => {
      console.log("取消订阅并退出...");
      await connection.removeOnLogsListener(subscriptionId);
      process.exit(0);
    });
  } catch (error) {
    console.error("订阅日志时出错:", error);
  }
}

// 执行订阅
subscribeToPumpFunLogs();