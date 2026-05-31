# Ataque Man in the Middle (MitM) mediante ARP Spoofing

## 1. Objetivo del Laboratorio

Comprender el funcionamiento del protocolo ARP (Address Resolution Protocol) y demostrar de manera práctica cómo un atacante puede explotar su falta de autenticación para realizar un ataque de **ARP Spoofing**, envenenando las tablas ARP de la víctima y el router para interceptar el tráfico entre ambos sin que ninguno lo detecte.

## 2. Objetivo del Script

El script `arp_mitm.py` automatiza el envío de **ARP Replies falsos** tanto a la víctima como al router, haciendo que ambos crean que la MAC del atacante corresponde al otro extremo de la comunicación. Esto coloca al atacante en medio del tráfico, permitiéndole interceptar, leer y modificar los paquetes que circulan entre la víctima y el router.

### 2.1 Parámetros del Script

| **Parámetro** | **Flag** | **Valor por Defecto** | **Descripción** |
| --- | --- | --- | --- |
| Interfaz de red | -i / --interfaz | eth0 | Interfaz desde la cual se envían los paquetes |
| IP de la víctima | -v / --victima | 10.0.99.50 | Dirección IP de la máquina víctima |
| IP del router | -r / --router | 10.0.99.1 | Dirección IP del gateway o servidor objetivo |
| Intervalo | -t / --intervalo | 2 seg | Tiempo de espera entre cada envío de paquetes ARP |

**Ejemplos de uso:**

```bash
# Uso básico (valores por defecto)
sudo python3 arp_mitm.py

# Especificar víctima y router
sudo python3 arp_mitm.py -v 10.0.99.50 -r 10.0.99.1

```

### 2.2 Requisitos para Utilizar la Herramienta

- **Sistema operativo:** Linux (preferiblemente Kali Linux)
- **Librería necesaria:** Scapy para manipulación de paquetes
- **Instalación:**

```bash
sudo apt update
sudo apt install python3-scapy -y
```

- **Privilegios:** ejecución como root (sudo)
- **Red:** estar en la misma red que la víctima y el router

## 3. Documentación del Funcionamiento del Script

### 3.1 Flujo General

```
INICIO
  │
  ├─► Verificar ejecución como root
  │
  ├─► Parsear argumentos (-i, -v, -r, -t)
  │
  ├─► Obtener MAC real de la víctima (ARP Request)
  ├─► Obtener MAC real del router (ARP Request)
  │
  ├─► Activar IP Forwarding
  │
  └─► BUCLE infinito
        │
        ├─► Enviar ARP Reply falso a la víctima
        ├─► Enviar ARP Reply falso al router
        └─► Esperar intervalo → repetir

FIN (Ctrl+C) ─► Restaurar tablas ARP → Desactivar IP Forwarding
```

### 3.2 Código del Script

**Parte 1 — Imports, configuración y funciones principales:**

[IMAGEN 1 - CODIGO SCRIPT PARTE 1]

**Parte 2 — Bucle de ataque, restauración y punto de entrada:**

[IMAGEN 2 - CODIGO SCRIPT PARTE 2]

### 3.3 ¿Cómo funciona el ARP Spoofing?

El protocolo ARP no tiene mecanismo de autenticación. Cuando un host recibe un ARP Reply, actualiza su tabla ARP sin verificar si la respuesta fue solicitada. El ataque explota esto enviando ARP Replies falsos continuamente:

| **Mensaje enviado a** | **Contenido falso** | **Efecto** |
| --- | --- | --- |
| Víctima | "El router `10.0.99.1` tiene la MAC del atacante" | La víctima envía su tráfico al atacante |
| Router | "La víctima `10.0.99.50` tiene la MAC del atacante" | El router responde al atacante |

El atacante queda en medio de toda la comunicación.

### 3.4 Funciones Principales

**`obtener_mac(ip, interfaz)`** — Envía un ARP Request a la red preguntando quién tiene esa IP y captura la respuesta para obtener su dirección MAC real. Si el host no responde, el script se detiene con un error.

**`envenenar_arp(ip_objetivo, mac_objetivo, ip_falsa, interfaz)`** — Envía un ARP Reply falso al objetivo diciéndole que una IP específica tiene la MAC del atacante, engañando así su tabla ARP para que redirija el tráfico hacia el atacante.

**`restaurar_arp(ip_objetivo, mac_objetivo, ip_real, mac_real, interfaz)`** — Cuando el ataque termina, envía ARP Replies con los valores correctos y reales para devolver las tablas ARP de la víctima y el router a su estado original, borrando el rastro del ataque.

**`habilitar_ip_forwarding()`** — Activa el reenvío de paquetes en Linux para que el tráfico interceptado siga llegando a su destino real, haciendo el ataque transparente e invisible para la víctima.

**`ejecutar_ataque(ip_victima, ip_router, interfaz, intervalo)`** — Bucle principal del ataque. Obtiene las MACs reales, activa el IP Forwarding y envía ARP falsos tanto a la víctima como al router en un ciclo continuo hasta que el usuario lo detiene con Ctrl+C.

**`main()`** — Punto de entrada del script. Verifica que se ejecuta como root, recoge los argumentos de la línea de comandos y lanza el ataque.

## 4. Documentación de la Red

### 4.1 Topología

[IMAGEN 1 - TOPOLOGIA GNS3]

### 4.2 Direccionamiento IP

| **Dispositivo** | **Rol** | **Interfaz** | **Dirección IP** | **Máscara** |
| --- | --- | --- | --- | --- |
| R1 | Router / Gateway | f0/0 | 10.0.99.1 | 255.255.255.0 |
| kali-linux-2025.3 | Atacante | eth0 | 10.0.99.100 | 255.255.255.0 |
| Clonekali-1 | Víctima | e0 | 10.0.99.50 | 255.255.255.0 |

### 4.3 Configuración del Router R1

[IMAGEN 2 - CONFIGURACION R1]

### 4.4 Conexiones del Switch1

| **Puerto Switch** | **Conectado a** | **Dispositivo** |
| --- | --- | --- |
| e0 | f0/0 | R1 (Router) |
| e1 | eth0 | kali-linux (Atacante) |
| e2 | e0 | Clonekali-1 (Víctima) |

## 5. Evidencia del Ataque

**Tabla ARP de la víctima — antes del ataque**

Se observa la tabla ARP normal de la víctima donde `10.0.99.1` tiene su MAC real `d0:01:07:20:00:00` y `10.0.99.150` tiene su MAC real `00:0c:29:62:61:41`.

[IMAGEN 3 - ARP VICTIMA ANTES]

**Verificación de la dirección IP y MAC del atacante**

Se verifica que la máquina atacante tiene la IP `10.0.99.100` y la MAC `00:0c:29:b0:f6:1c` en la interfaz `eth0`.

[IMAGEN 4 - IP A ATACANTE]

**Ejecución del script en la máquina atacante**

Se inicia el ataque con el comando `sudo python3 arp_mitm.py`. El script obtiene las MACs reales de la víctima y el router, activa el IP Forwarding y comienza a enviar ARP Replies falsos en bucle.

[IMAGEN 5 - SCRIPT CORRIENDO]

**Verificación del ataque en Wireshark — filtro ARP**

Se observa el envenenamiento ARP en tiempo real. El atacante `VMware_b0:f6:1c` envía continuamente ARP Replies falsos a la víctima `VMware_a0:0a:51` indicando que `10.0.99.1 is at 00:0c:29:b0:f6:1c` (MAC del atacante). Wireshark detecta el conflicto con el mensaje `duplicate use of 10.0.99.1 detected`.

[IMAGEN 6 - WIRESHARK ARP]

**Tabla ARP de la víctima — después del ataque**

Se confirma el envenenamiento exitoso. La segunda ejecución de `arp -n` muestra que `10.0.99.1` ahora tiene la MAC `00:0c:29:b0:f6:1c` que corresponde al atacante, en lugar de la MAC real del router.

[IMAGEN 7 - ARP VICTIMA DESPUES]

**Finalización del ataque y restauración de tablas ARP**

Al presionar Ctrl+C el script restaura automáticamente las tablas ARP de la víctima y el router a sus valores originales y desactiva el IP Forwarding, dejando la red en su estado normal.

[IMAGEN 8 - SCRIPT FINALIZADO]

## 6. Contramedidas

### 6.1 ARP Inspection Dinámica (DAI)

Es la principal defensa contra ARP Spoofing. El switch valida los paquetes ARP contra una tabla de enlaces IP-MAC confiables (DHCP Snooping Binding Table) y descarta los que no coinciden.

```
Switch(config)# ip arp inspection vlan 1
Switch(config)# interface e0
Switch(config-if)# ip arp inspection trust
```

### 6.2 Entradas ARP Estáticas

Configurar manualmente las entradas ARP críticas en los hosts evita que sean modificadas por ARP Replies falsos.

```bash
# En la víctima, fijar la MAC real del router
sudo arp -s 10.0.99.1 d0:01:07:20:00:00
```

### 6.3 Segmentación con VLANs

Dividir la red en VLANs limita el alcance del ataque, ya que el ARP Spoofing solo funciona dentro del mismo segmento de red.

### 6.4 Monitoreo con herramientas de detección

Herramientas como **ARPwatch** detectan cambios inesperados en las tablas ARP y alertan al administrador.

```bash
sudo apt install arpwatch -y
sudo arpwatch -i eth0
```

| **Contra-medida** | **Efectividad** | **Dónde se aplica** |
| --- | --- | --- |
| ARP Inspection Dinámica (DAI) | ⭐⭐⭐⭐⭐ Muy alta | Switch |
| Entradas ARP estáticas | ⭐⭐⭐⭐ Alta | Hosts |
| Segmentación con VLANs | ⭐⭐⭐ Media | Switch |
| ARPwatch (monitoreo) | ⭐⭐⭐ Media | Servidor/Host |
| HTTPS / Cifrado | ⭐⭐⭐⭐ Alta | Aplicaciones |
