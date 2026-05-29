# Ataque de Agotamiento DHCP (DHCP Starvation)

## 1. Objetivo del Laboratorio

Comprender el funcionamiento del protocolo DHCP (Dynamic Host Configuration Protocol) y demostrar de manera práctica cómo un atacante puede explotar su falta de autenticación para realizar un ataque de **DHCP Starvation**, agotando el pool de direcciones IP disponibles en el servidor DHCP y dejando a los clientes legítimos de la red sin posibilidad de obtener configuración de red.

## 2. Objetivo del Script

El script `dhcp_starvation.py` automatiza el envío masivo de solicitudes **DHCP DISCOVER** utilizando **direcciones MAC falsificadas (spoofed)** generadas aleatoriamente. Cada solicitud aparenta ser un cliente legítimo diferente, por lo que el servidor DHCP reserva una dirección IP para cada una, agotando progresivamente su pool hasta que no puede atender a clientes reales.

### 2.1 Parámetros del Script

| **Parámetro** | **Flag** | **Valor por Defecto** | **Descripción** |
| --- | --- | --- | --- |
| Interfaz de red | -i / --interfaz | eth0 | Interfaz desde la cual se envían los paquetes |
| Cantidad de paquetes | -n / --cantidad | 1000 | Número total de DHCP DISCOVER a enviar |
| Delay entre paquetes | -d / --delay | 0.05 seg | Tiempo de espera entre cada paquete |
| Modo silencioso | -q / --quiet | Desactivado | Suprime la impresión de cada paquete en pantalla |

**Ejemplos de uso:**

```bash
# Uso básico (valores por defecto)
sudo python3 dhcp_starvation.py

# Especificar interfaz y 500 paquetes
sudo python3 dhcp_starvation.py -i eth0 -n 500

# Ataque rápido sin delay en modo silencioso
sudo python3 dhcp_starvation.py -i eth0 -n 1000 -d 0 -q
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
- **Red:** estar en la misma red que el servidor DHCP

## 3. Documentación del Funcionamiento del Script

### 3.1 Flujo General

```
INICIO
  │
  ├─► Verificar ejecución como root
  │
  ├─► Parsear argumentos (-i, -n, -d, -q)
  │
  └─► BUCLE (i = 1 hasta cantidad)
        │
        ├─► Generar MAC aleatoria con RandMAC()
        ├─► Construir paquete DHCP DISCOVER
        ├─► Enviar paquete por capa 2 (sendp)
        └─► Esperar delay → repetir

FIN ─► Mostrar resumen de paquetes enviados
```

### 3.2 Código del Script

**Parte 1 — Imports, configuración y construcción del paquete:**

[IMAGEN 1]

**Parte 2 — Bucle de ataque, manejo de argumentos y punto de entrada:**

[IMAGEN 2]

**Ejecución del script:**

[IMAGEN 3]

### 3.3 Proceso DORA y por qué el ataque funciona

El protocolo DHCP sigue 4 pasos normales:

| **Paso** | **Mensaje** | **Dirección** |
| --- | --- | --- |
| 1 | **DISCOVER** | Cliente → Broadcast |
| 2 | **OFFER** | Servidor → Cliente |
| 3 | **REQUEST** | Cliente → Broadcast |
| 4 | **ACK** | Servidor → Cliente |

El ataque explota el paso 1: se envían miles de DISCOVER con MACs distintas. El servidor reserva una IP por cada MAC sin que el atacante complete el proceso, agotando el pool completo.

### 3.4 Funciones Principales

**`construir_dhcp_discover(mac_falsa)`** — Recibe una MAC aleatoria, la convierte a bytes y construye el paquete DHCP DISCOVER en capas con Scapy.

**`ejecutar_ataque(interfaz, cantidad, delay, verbose)`** — Bucle principal del ataque: genera una MAC nueva por iteración, construye el paquete, lo envía por capa 2 con `sendp()` y muestra el resumen al finalizar.

**`main()`** — Punto de entrada: verifica permisos de root, parsea los argumentos de línea de comandos y llama a `ejecutar_ataque()`.

## 4. Documentación de la Red

### 4.1 Topología

[IMAGEN 4]

### 4.2 Direccionamiento IP

| **Dispositivo** | **Rol** | **Interfaz** | **Dirección IP** | **Máscara** |
| --- | --- | --- | --- | --- |
| R1 | Router / Servidor DHCP | e0/0 | 10.0.99.1 | 255.255.255.0 |
| kali-linux-2025.3 | Atacante | eth0 | 10.0.99.100 | 255.255.255.0 |
| Clonekali-1 | Víctima | e0 | Dinámica (DHCP) | 255.255.255.0 |

### 4.3 Configuración del Pool DHCP en R1

[IMAGEN 5]

| **Parámetro** | **Valor** |
| --- | --- |
| Nombre del pool | ATAQUE |
| Red | 10.0.99.0/24 |
| Gateway por defecto | 10.0.99.1 |
| Servidor DNS | 8.8.8.8 |
| Rango disponible | 10.0.99.2 – 10.0.99.254 (253 IPs) |

### 4.4 Conexiones del Switch1

| **Puerto Switch** | **Conectado a** | **Dispositivo** |
| --- | --- | --- |
| e0 | e0/0 | R1 (Router) |
| e1 | eth0 | kali-linux (Atacante) |
| e2 | e0 | Clonekali-1 (Víctima) |

## 5. Funcionamiento del ataque

**(Wireshark — antes del ataque)**

Se ve tráfico DHCP normal: un DHCP Request desde 0.0.0.0 y el servidor 10.0.99.1 respondiendo con un DHCP ACK asignando 10.0.99.2. La red funciona correctamente.

[IMAGEN 6]

**(Wireshark — durante el ataque)**

Se ve la inundación masiva de DHCP Discover desde 0.0.0.0 hacia 255.255.255.255, todos con Transaction IDs distintos. Esto es el script enviando MACs falsas una tras otra agotando el pool.

[IMAGEN 7]

**(Víctima — impacto del ataque)**

La máquina víctima intenta reconectarse con `nmcli device connect eth0` y recibe el error: `IP configuration could not be reserved (no available address, timeout)` — El pool está completamente agotado. La víctima no puede obtener IP.

[IMAGEN 8]

## 6. Contramedidas

### 6.1 DHCP Snooping

Es la principal defensa contra servidores DHCP no autorizados. El switch clasifica los puertos como:

- **Trusted:** conectados al servidor DHCP legítimo.
- **Untrusted:** conectados a clientes.

Solo los puertos confiables pueden enviar respuestas DHCP, bloqueando ofertas provenientes de dispositivos no autorizados.

### 6.2 Port Security

Limita la cantidad de direcciones MAC permitidas por puerto, dificultando el uso masivo de MAC falsas y reduciendo el impacto de ataques de inundación.

### 6.3 Reservas y exclusiones DHCP

Consiste en reservar direcciones IP para dispositivos críticos y excluir determinados rangos del pool dinámico, garantizando la disponibilidad de recursos esenciales incluso ante incidentes en el servicio DHCP.
