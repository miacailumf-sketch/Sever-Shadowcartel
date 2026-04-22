const { Client, GatewayIntentBits } = require('discord.js');
const mongoose = require('mongoose');
const express = require('express');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 10000;

// Tạo web server ảo để Render không giết bot
app.get('/', (req, res) => res.send('Sever-Shadowcartel is ONLINE!'));
app.listen(port, () => console.log(`Web chạy trên port ${port}`));

// Kết nối MongoDB
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('Đã kết nối MongoDB thành công!'))
  .catch(err => console.error('Lỗi kết nối MongoDB:', err));

// Khởi tạo Bot Discord
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

client.once('ready', () => {
  console.log(`Đã đăng nhập thành công: ${client.user.tag}`);
});

// Code xử lý của Đại ca viết thêm ở dưới này...
client.on('messageCreate', message => {
  if (message.content === 'ping') {
    message.reply('Pong! Shadow Cartel vạn tuế!');
  }
});

client.login(process.env.TOKEN);
