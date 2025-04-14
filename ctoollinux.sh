#!/bin/bash

# CraigTool - Blue Hat Terminal Toolkit

clear

# BANNER
echo "_________               .__     ___________           .__    ._._._."
echo "\_   ___ \____________  |__| ___\__    ___/___   ____ |  |   | | | |"
echo "/    \  \/\_  __ \__  \ |  |/ ___\|    | /  _ \ /  _ \|  |   | | | |"
echo "\     \____|  | \// __ \|  / /_/  >    |(  <_> |  <_> )  |__  \|\|\|"
echo " \______  /|__|  (____  /__\___  /|____| \____/ \____/|____/  ______"
echo "        \/            \/  /_____/                             \/\/\/"
echo ""
echo "  Welcome to CraigTool – Blue Hat Ops Command Central 🛡️"
echo ""

# Menu
PS3="Pick your weapon, Defender >> "
options=("Recon Scanner" "Threat Intel Pull" "Process Sniffer" "YARA Scan" "Firewall Audit" "Rootkit Check" "Log Forensics" "Memory Hunt" "Utility Box" "Exit")
select opt in "${options[@]}"; do
    case $opt in
        "Recon Scanner")
            echo "[*] Starting Recon..."
            read -p "Enter target domain/IP: " target
            echo "[+] Nmap scan on $target"
            nmap -sV -T4 $target
            echo "[+] Whois info:"
            whois $target
            ;;
        "Threat Intel Pull")
            echo "[*] Pulling latest bad IPs from abuse.ch (if curl installed)..."
            curl -s https://feodotracker.abuse.ch/downloads/ipblocklist_recommended.txt | head -n 20
            ;;
        "Process Sniffer")
            echo "[*] Listing suspicious processes..."
            ps aux | grep -E 'nc|ncat|python|perl|bash' | grep -v grep
            ;;
        "YARA Scan")
            echo "[*] Running YARA (ensure installed)..."
            read -p "Enter directory to scan: " path
            yara -r /usr/local/yara_rules/index.yar $path
            ;;
        "Firewall Audit")
            echo "[*] Current iptables rules:"
            sudo iptables -L
            ;;
        "Rootkit Check")
            echo "[*] Scanning for rootkits..."
            sudo rkhunter --check
            ;;
        "Log Forensics")
            echo "[*] Showing last 50 suspicious auth.log entries..."
            sudo grep 'Failed\|Invalid' /var/log/auth.log | tail -n 50
            ;;
        "Memory Hunt")
            echo "[*] Strings from memory (warning: noisy!)"
            sudo strings /dev/mem | grep -i "password\|api_key\|token"
            ;;
        "Utility Box")
            echo "[*] Encoding tools:"
            read -p "Enter string to encode: " data
            echo "Base64: $(echo $data | base64)"
            echo "Hex: $(echo -n $data | xxd -p)"
            ;;
        "Exit")
            echo "Peace out, Defender. CraigTool signing off 🛡️🦅"
            break
            ;;
        *) echo "⚠️ Invalid option. Try again.";;
    esac
done
