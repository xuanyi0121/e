#!/bin/bash

#安装docker
wget -qO- get.docker.com | bash

#查看docker版本
docker -v

# 设置开机自动启动
systemctl enable docker

#修改Docker配置（可选）
cat > /etc/docker/daemon.json <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "20m",
        "max-file": "3"
    },
    "ipv6": true,
    "fixed-cidr-v6": "fd00:dead:beef:c0::/80",
    "experimental":true,
    "ip6tables":true
}
EOF

#重启 Docker 服务
systemctl restart docker

#Docker ChatGPT 部署命令
echo "开始部署ChatGPT"
read -p "请输入您的APT: " API
sudo docker run \
    --name chatgpt-web \
    -p 3002:3002 \
    --env OPENAI_API_KEY=${APT} \
    --restart always \
    -d teemo/chatgpt-web:latest

#安装caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list

sudo apt update

sudo apt install caddy

#查看是否安装成功
caddy version

#启动caddy
sudo systemctl daemon-reload
sudo systemctl enable caddy
sudo systemctl start caddy

# 提示用户输入域名、IP和端口号
read -p "请输入您的域名: " domain
read -p "请输入您的IP地址: " ip
read -p "请输入您的端口号: " port

# 生成反向代理规则串
config="\"${domain}\" {\n"
config+="\treverse_proxy ${ip}:${port}\n"
config+="}"

# 将反向代理规则写入Caddyfile
echo -e "${config}" | sudo tee /etc/caddy/Caddyfile && systemctl reload caddy
