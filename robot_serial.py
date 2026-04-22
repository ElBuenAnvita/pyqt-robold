import time
import serial
import serial.tools.list_ports


class BrazoRoboticoMarlin:
    def __init__(self):
        self.serial_port = None

    # =========================
    # CONEXIÓN SERIAL
    # =========================
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
            return True
        print("⚠️ Intento de envío sin conexión")
        return False

    def leer_datos(self):
        if self.is_conectado() and self.serial_port.in_waiting > 0:
            respuesta = self.serial_port.readline().decode("utf-8", errors="ignore").strip()
            if respuesta == "wait" or respuesta.startswith("ok"):
                return None
            return respuesta
        return None

    def log(self, mensaje, log_callback=None):
        if log_callback:
            log_callback(mensaje)
        else:
            print(mensaje)

    # =========================
    # CONTROL Y UTILIDADES
    # =========================
    def solicitar_posicion(self):
        return self.enviar_comando("M114")

    def detener_servo(self):
        return self.enviar_comando("M280 P0 S-1")

    def fijar_cero_y_limites(self):
        if not self.is_conectado():
            print("⚠️ No conectado")
            return False

        self.enviar_comando("M211 S0")
        time.sleep(0.2)
        self.enviar_comando("G92 X0 Y0 Z0 E0")
        self.solicitar_posicion()
        return True

    def homing(self):
        if not self.is_conectado():
            print("⚠️ No conectado")
            return False
        self.enviar_comando("G28")
        return True

    def cambiar_velocidad(self, porcentaje):
        return self.enviar_comando(f"M220 S{porcentaje}")

    # =========================
    # MOVIMIENTO SIMPLE (COMPAT)
    # =========================
    def mover_eje(self, eje_id, valor_grados):
        if not self.is_conectado():
            print("⚠️ No conectado")
            return False

        if eje_id == "Servo":
            self.enviar_comando(f"M280 P0 S{int(valor_grados)}")
            return True

        return self._mover_eje(eje_id, float(valor_grados), log_callback=None)

    # =========================
    # MACROS / RUTINAS GRABADAS
    # =========================
    def ejecutar_movimiento(self, movimiento, log_callback=None):
        if not self.is_conectado():
            self.log("⚠️ No conectado", log_callback)
            return False

        tipo = movimiento.get("tipo", "eje")

        if tipo == "eje":
            eje_id = movimiento["eje"]
            grados = float(movimiento["grados"])
            return self._mover_eje(eje_id, grados, log_callback)

        if tipo == "servo_timed":
            accion = movimiento.get("accion", "servo")
            pwm = int(movimiento["pwm"])
            duracion_ms = int(movimiento.get("duracion_ms", 3000))
            return self._mover_servo_timed(accion, pwm, duracion_ms, log_callback)

        self.log(f"Tipo de movimiento no soportado: {tipo}", log_callback)
        return False

    def ejecutar_secuencia(self, secuencia, log_callback=None, invertir=False):
        if not self.is_conectado():
            self.log("⚠️ No conectado", log_callback)
            return False

        movimientos = [dict(m) for m in secuencia]
        if invertir:
            movimientos = [self._invertir_movimiento(m) for m in reversed(movimientos)]

        for movimiento in movimientos:
            ok = self.ejecutar_movimiento(movimiento, log_callback=log_callback)
            if not ok:
                return False
        return True

    def _invertir_movimiento(self, movimiento):
        m = dict(movimiento)
        tipo = m.get("tipo", "eje")

        if tipo == "eje":
            m["grados"] = -float(m.get("grados", 0))
            return m

        if tipo == "servo_timed":
            accion_original = m.get("accion", "abrir")
            velocidad_pct = int(m.get("velocidad_pct", 100))
            delta = int(velocidad_pct * 0.9)

            # Ajustado al sentido que definiste en la app:
            # abrir = 90 - delta
            # cerrar = 90 + delta
            if accion_original == "abrir":
                accion = "cerrar"
                pwm = 90 + delta
            else:
                accion = "abrir"
                pwm = 90 - delta

            return {
                "tipo": "servo_timed",
                "accion": accion,
                "pwm": pwm,
                "duracion_ms": int(m.get("duracion_ms", 3000)),
                "velocidad_pct": velocidad_pct,
            }

        return m

    # =========================
    # AYUDANTES INTERNOS
    # =========================
    def _mover_eje(self, eje_id, grados, log_callback=None):
        self.enviar_comando("G91")

        if eje_id == "T":
            self.enviar_comando("T0")
            self.enviar_comando(f"G1 E{grados} F2000")
        elif eje_id == "E":
            self.enviar_comando("T1")
            self.enviar_comando(f"G1 E{grados} F2000")
        else:
            self.enviar_comando(f"G1 {eje_id}{grados} F2000")

        self.solicitar_posicion()
        signo = "+" if grados > 0 else ""
        self.log(f"Ejecutado: {eje_id} = {signo}{grados}°.", log_callback)
        time.sleep(0.12)
        return True

    def _mover_servo_timed(self, accion, pwm, duracion_ms, log_callback=None):
        self.enviar_comando(f"M280 P0 S{pwm}")
        self.log(f"Garra {accion}: PWM {pwm} durante {duracion_ms} ms.", log_callback)
        time.sleep(max(duracion_ms, 0) / 1000.0)
        self.detener_servo()
        self.log("Servo detenido (M280 P0 S-1).", log_callback)
        time.sleep(0.15)
        return True

    def _ir_al_centro_xy(self):
        self.enviar_comando("G90")
        self.enviar_comando("G0 X0 Y0")
        self.enviar_comando("M400")
        time.sleep(0.3)
        self.enviar_comando("G91")

    # =========================
    # RUTINAS ESPECIALES
    # =========================
    def mover_centro_izquierda(self, log_callback=None):
        if not self.is_conectado():
            self.log("⚠️ No conectado", log_callback)
            return False

        self.log("Centro → Izquierda: yendo al centro...", log_callback)
        self._ir_al_centro_xy()

        ida = []
        for i in range(7):
            ida.append({"tipo": "eje", "eje": "X", "grados": -5})
            if (i + 1) % 2 == 0:
                ida.append({"tipo": "eje", "eje": "Y", "grados": -15})

        self.log("Centro → Izquierda: ida...", log_callback)
        self.ejecutar_secuencia(ida, log_callback=log_callback, invertir=False)
        self.log("Centro → Izquierda: regreso...", log_callback)
        self.ejecutar_secuencia(ida, log_callback=log_callback, invertir=True)
        self.log("Centro → Izquierda completado.", log_callback)
        return True

    def mover_base_izquierda(self, log_callback=None):
        if not self.is_conectado():
            self.log("⚠️ No conectado", log_callback)
            return False

        self.log("Base → Izquierda: yendo al centro...", log_callback)
        self._ir_al_centro_xy()
        self.enviar_comando("T0")

        ida = []
        for i in range(7):
            ida.append({"tipo": "eje", "eje": "X", "grados": -5})
            if i < 3:
                ida.append({"tipo": "eje", "eje": "T", "grados": 30})

        self.log("Base → Izquierda: ida...", log_callback)
        self.ejecutar_secuencia(ida, log_callback=log_callback, invertir=False)
        self.log("Base → Izquierda: regreso...", log_callback)
        self.ejecutar_secuencia(ida, log_callback=log_callback, invertir=True)
        self.log("Base → Izquierda completado.", log_callback)
        return True