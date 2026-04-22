import serial
import serial.tools.list_ports
import time


class BrazoRoboticoMarlin:
    def __init__(self):
        self.serial_port = None

    def obtener_puertos_disponibles(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def conectar(self, puerto, baudrate=115200):
        if self.serial_port is None or not self.serial_port.is_open:
            try:
                self.serial_port = serial.Serial(puerto, baudrate, timeout=0.1)
                time.sleep(2)
                print("Conexión establecida")
                return True, "Conectado"
            except Exception as e:
                return False, str(e)
        return False, "Ya estaba conectado"

    def desconectar(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("Desconectado")

    def is_conectado(self):
        return self.serial_port is not None and self.serial_port.is_open

    def enviar_comando(self, comando):
        if self.is_conectado():
            self.serial_port.write(f"{comando}\n".encode("utf-8"))
            print(f"Enviado: {comando}")
        else:
            print("⚠️ Intento de envío sin conexión")

    def leer_datos(self):
        if self.is_conectado() and self.serial_port.in_waiting > 0:
            respuesta = self.serial_port.readline().decode("utf-8", errors="ignore").strip()
            if respuesta == "wait" or respuesta.startswith("ok"):
                return None
            return respuesta
        return None

    # =========================
    # MOVIMIENTOS GENERALES
    # =========================
    def mover_eje(self, eje_id, valor_grados):
        if not self.is_conectado():
            print("⚠️ No conectado")
            return

        if eje_id == "Servo":
            self.enviar_comando(f"M280 P0 S{valor_grados}")
            return

        unidades = valor_grados
        self.enviar_comando("G91")

        if eje_id == "T":
            self.enviar_comando("T0")
            self.enviar_comando(f"G1 E{unidades} F2000")
        elif eje_id == "E":
            self.enviar_comando("T1")
            self.enviar_comando(f"G1 E{unidades} F2000")
        else:
            self.enviar_comando(f"G1 {eje_id}{unidades} F2000")

        self.solicitar_posicion()

    # =========================
    # AYUDANTES INTERNOS
    # =========================
    def _ir_al_centro_xy(self):
        self.enviar_comando("G90")
        self.enviar_comando("G0 X0 Y0")
        self.enviar_comando("M400")
        time.sleep(0.3)
        self.enviar_comando("G91")

    def _mover_relativo(self, comando, pausa=0.12):
        self.enviar_comando(comando)
        self.enviar_comando("M400")
        time.sleep(pausa)

    # =========================
    # RUTINAS ESPECIALES
    # =========================
    def mover_centro_izquierda(self):
        """
        Ida y regreso:
        - Va al centro
        - Ida: 7 pasos de X = -5
        - En pasos pares: Y = -15
        - Regreso: deshace la trayectoria en orden inverso
        """
        if not self.is_conectado():
            print("⚠️ No conectado")
            return

        print("Iniciando movimiento Centro → Izquierda (ida y vuelta)")
        self._ir_al_centro_xy()

        # IDA
        print("--- IDA Centro → Izquierda ---")
        for paso in range(1, 8):
            self._mover_relativo("G1 X-5 F2000")
            print(f"Paso {paso}: X = -5")

            if paso % 2 == 0:
                self._mover_relativo("G1 Y-15 F2000")
                print(f"Paso {paso}: Y = -15")

        # REGRESO (inverso de la trayectoria)
        print("--- REGRESO Izquierda → Centro ---")
        for paso in range(7, 0, -1):
            if paso % 2 == 0:
                self._mover_relativo("G1 Y15 F2000")
                print(f"Paso {paso}: Y = +15")

            self._mover_relativo("G1 X5 F2000")
            print(f"Paso {paso}: X = +5")

        self.enviar_comando("M400")
        self.solicitar_posicion()
        print("Movimiento Centro → Izquierda con regreso FINALIZADO")

    def mover_base_izquierda(self):
        """
        Ida y regreso:
        - Parte del centro
        - Ida: 7 pasos de X = -5
        - Base T0 (eje E): +30° en los pasos 1, 2 y 3
        - Regreso: deshace primero la base cuando corresponde y luego X
        """
        if not self.is_conectado():
            print("⚠️ No conectado")
            return

        print("Iniciando movimiento Base → Izquierda (ida y vuelta)")
        self._ir_al_centro_xy()
        self.enviar_comando("T0")

        # IDA
        print("--- IDA Base → Izquierda ---")
        for paso in range(1, 8):
            self._mover_relativo("G1 X-5 F2000")
            print(f"Paso {paso}: X = -5")

            if paso <= 3:
                self._mover_relativo("G1 E30 F2000")
                print(f"Paso {paso}: Base T = +30°")

        # REGRESO (inverso de la trayectoria)
        print("--- REGRESO Izquierda → Base/Centro ---")
        for paso in range(7, 0, -1):
            if paso <= 3:
                self._mover_relativo("G1 E-30 F2000")
                print(f"Paso {paso}: Base T = -30°")

            self._mover_relativo("G1 X5 F2000")
            print(f"Paso {paso}: X = +5")

        self.enviar_comando("M400")
        self.solicitar_posicion()
        print("Movimiento Base → Izquierda con regreso FINALIZADO")

    # =========================
    # CONTROL Y UTILIDADES
    # =========================
    def solicitar_posicion(self):
        self.enviar_comando("M114")

    def detener_servo(self):
        self.enviar_comando("M280 P0 S-1")

    def fijar_cero_y_limites(self):
        if not self.is_conectado():
            print("⚠️ No conectado")
            return

        self.enviar_comando("M211 S0")
        print("Límites desactivados")
        time.sleep(0.2)

        self.enviar_comando("G92 X0 Y0 Z0 E0")
        print("Coordenadas en cero")

        self.solicitar_posicion()

    def homing(self):
        if not self.is_conectado():
            print("⚠️ No conectado")
            return

        self.enviar_comando("G28")
        print("Homing ejecutado")

    def cambiar_velocidad(self, porcentaje):
        self.enviar_comando(f"M220 S{porcentaje}")
