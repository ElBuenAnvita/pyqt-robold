import serial
import serial.tools.list_ports

class BrazoRoboticoMarlin:
    def __init__(self):
        self.serial_port = None

    def obtener_puertos_disponibles(self):
        """Escanea los puertos COM de Windows/Linux"""
        return [p.device for p in serial.tools.list_ports.comports()]

    def conectar(self, puerto, baudrate=115200):
        """Abre la conexión serial"""
        if self.serial_port is None or not self.serial_port.is_open:
            try:
                self.serial_port = serial.Serial(puerto, baudrate, timeout=0.1)
                return True, "Conectado"
            except Exception as e:
                return False, str(e)
        return False, "Ya estaba conectado"

    def desconectar(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def is_conectado(self):
        return self.serial_port is not None and self.serial_port.is_open

    def enviar_comando(self, comando):
        """Envía el texto crudo a la TinyBee"""
        if self.is_conectado():
            self.serial_port.write(f"{comando}\n".encode('utf-8'))
            print(f"Enviado: {comando}")

    def leer_datos(self):
        """Lee el buffer del serial filtrando basura y acuses de recibo"""
        if self.is_conectado() and self.serial_port.in_waiting > 0:
            respuesta = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
            # Ignoramos la basura o los OK simples
            if respuesta == "wait" or respuesta.startswith("ok"):
                return None
            return respuesta
        return None

    # --- RUTINAS DE MOVIMIENTO (G-CODE) ---
    def mover_eje(self, eje_id, valor_grados):
        if not self.is_conectado(): return
        
        if eje_id == "Servo":
            self.enviar_comando(f"M280 P0 S{valor_grados}")
            return

        unidades = valor_grados  # / 2 (Su factor de conversión si lo necesitan)
        self.enviar_comando("G91") # Modo Relativo
        
        if eje_id == "T":
            self.enviar_comando("T0")
            self.enviar_comando(f"G1 E{unidades} F2000")
        elif eje_id == "E":
            self.enviar_comando("T1")
            self.enviar_comando(f"G1 E{unidades} F2000")
        else:
            self.enviar_comando(f"G1 {eje_id}{unidades} F2000")
        
        self.solicitar_posicion() # Pedimos a Marlin que confirme dónde quedó

    def solicitar_posicion(self):
        self.enviar_comando("M114")

    def detener_servo(self):
        self.enviar_comando("M280 P0 S-1")

    def fijar_cero_y_limites(self):
        self.enviar_comando("M211 S0")
        self.enviar_comando("G92 X0 Y0 Z0 E0")
        self.solicitar_posicion()

    def cambiar_velocidad(self, porcentaje):
        self.enviar_comando(f"M220 S{porcentaje}")