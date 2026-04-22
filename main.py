import json
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer

from gui_layout import InterfazBrazoUI
from robot_serial import BrazoRoboticoMarlin


class ControladorPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Brazo 6DOF - Robolds")
        self.setFixedSize(760, 820)

        self.ui = InterfazBrazoUI()
        self.setCentralWidget(self.ui)
        self.robot = BrazoRoboticoMarlin()

        self.timer_serial = QTimer()
        self.timer_serial.timeout.connect(self.rutina_lectura)

        self.timer_garra = QTimer()
        self.timer_garra.setSingleShot(True)
        self.timer_garra.timeout.connect(self.robot.detener_servo)

        self.base_dir = Path(__file__).resolve().parent
        self.archivo_log = self.base_dir / "registro_brazo.log"
        self.archivo_rutina = self.base_dir / "rutina_quemada.json"

        self.movimientos_actuales = []
        self.rutina_quemada = []
        self.cargar_rutina_quemada()

        self.actualizar_lista_puertos()
        self.conectar_eventos()
        self.agregar_log("--- Sistema de Control Listo ---")
        self.agregar_log("Por favor, conecte el puerto de la TinyBee.")

    def conectar_eventos(self):
        self.ui.btn_conectar.clicked.connect(self.toggle_conexion)
        self.ui.btn_leer_pos.clicked.connect(self.solicitar_posicion)
        self.ui.btn_fijar_cero.clicked.connect(self.fijar_cero)
        self.ui.btn_stop.clicked.connect(self.detener_servo)
        self.ui.btn_centro_izq.clicked.connect(self.centro_izquierda)
        self.ui.btn_base_izq.clicked.connect(self.base_izquierda)

        self.ui.btn_regresar_manual.clicked.connect(self.regresar_movimientos_manuales)
        self.ui.btn_quemar_rutina.clicked.connect(self.quemar_rutina)
        self.ui.btn_ejecutar_rutina.clicked.connect(self.ejecutar_rutina_quemada)
        self.ui.btn_limpiar_rutina.clicked.connect(self.limpiar_rutina)

        self.ui.slider_velocidad.valueChanged.connect(self.al_cambiar_velocidad)
        self.ui.slider_vel_garra.valueChanged.connect(self.al_cambiar_vel_garra)
        self.ui.btn_abrir_garra.clicked.connect(self.abrir_garra)
        self.ui.btn_cerrar_garra.clicked.connect(self.cerrar_garra)

        for eje_id, btn in self.ui.botones_mover.items():
            btn.clicked.connect(lambda checked, e=eje_id: self.ejecutar_movimiento(e))

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def agregar_log(self, mensaje):
        linea = f"[{self.timestamp()}] {mensaje}"
        actual = self.ui.txt_log.toPlainText()
        if actual.strip():
            self.ui.txt_log.setPlainText(linea + "\n" + actual)
        else:
            self.ui.txt_log.setPlainText(linea)

        with self.archivo_log.open("a", encoding="utf-8") as f:
            f.write(linea + "\n")

    def actualizar_lista_puertos(self):
        puertos = self.robot.obtener_puertos_disponibles()
        self.ui.combo_puertos.clear()
        self.ui.combo_puertos.addItems(puertos)

    def toggle_conexion(self):
        if not self.robot.is_conectado():
            puerto = self.ui.combo_puertos.currentText()
            exito, mensaje = self.robot.conectar(puerto)
            if exito:
                self.ui.lbl_estado.setText("Conectado")
                self.ui.lbl_estado.setStyleSheet("color: green; font-weight: bold;")
                self.ui.btn_conectar.setText("Desconectar")
                self.timer_serial.start(100)
                self.agregar_log(f"Conectado correctamente a la TinyBee en {puerto}.")
            else:
                self.ui.lbl_estado.setText(f"Error: {mensaje}")
                self.agregar_log(f"Error de conexión: {mensaje}")
        else:
            self.timer_serial.stop()
            self.robot.desconectar()
            self.ui.lbl_estado.setText("Desconectado")
            self.ui.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
            self.ui.btn_conectar.setText("Conectar")
            self.agregar_log("Desconectado.")

    def al_cambiar_velocidad(self):
        valor = self.ui.slider_velocidad.value()
        self.ui.lbl_velocidad_val.setText(f"{valor}%")
        self.robot.cambiar_velocidad(valor)
        self.agregar_log(f"Velocidad global ajustada a {valor}%.")

    def al_cambiar_vel_garra(self):
        valor = self.ui.slider_vel_garra.value()
        self.ui.lbl_vel_garra_val.setText(f"{valor}%")

    def solicitar_posicion(self):
        self.robot.solicitar_posicion()
        self.agregar_log("Solicitando coordenadas actuales (M114)...")

    def fijar_cero(self):
        self.robot.fijar_cero_y_limites()
        self.agregar_log("Límites desactivados (M211 S0).")
        self.agregar_log("Coordenadas fijadas en cero (G92 X0 Y0 Z0 E0).")

    def detener_servo(self):
        self.robot.detener_servo()
        self.agregar_log("Servo detenido (M280 P0 S-1).")

    def centro_izquierda(self):
        if self.robot.is_conectado():
            self.agregar_log("Iniciando rutina Centro → Izquierda (ida y vuelta).")
            self.robot.mover_centro_izquierda()
            self.agregar_log("Rutina Centro → Izquierda finalizada.")
        else:
            self.agregar_log("Error: Robot no conectado.")

    def base_izquierda(self):
        if self.robot.is_conectado():
            self.agregar_log("Iniciando rutina Base → Izquierda (ida y vuelta).")
            self.robot.mover_base_izquierda()
            self.agregar_log("Rutina Base → Izquierda finalizada.")
        else:
            self.agregar_log("Error: Robot no conectado.")

    def abrir_garra(self):
        velocidad_pct = self.ui.slider_vel_garra.value()
        valor_pwm = int(90 - (velocidad_pct * 0.9))
        self.robot.mover_eje("Servo", valor_pwm)
        self.timer_garra.start(3000)
        self.agregar_log(f"Garra abriendo. PWM enviado: {valor_pwm}.")

    def cerrar_garra(self):
        velocidad_pct = self.ui.slider_vel_garra.value()
        valor_pwm = int(90 + (velocidad_pct * 0.9))
        self.robot.mover_eje("Servo", valor_pwm)
        self.timer_garra.start(3000)
        self.agregar_log(f"Garra cerrando. PWM enviado: {valor_pwm}.")

    def ejecutar_movimiento(self, eje_id):
        try:
            texto_ingresado = self.ui.inputs[eje_id].text()
            grados = float(texto_ingresado)
        except ValueError:
            self.agregar_log(f"Valor inválido para el eje {eje_id}.")
            return

        exito = self.robot.mover_eje(eje_id, grados)
        if not exito:
            self.agregar_log("Error: Robot no conectado.")
            return

        self.movimientos_actuales.append({"eje": eje_id, "grados": grados})
        signo = "+" if grados > 0 else ""
        self.agregar_log(f"Movimiento manual guardado: {eje_id} = {signo}{grados}°.")

    def regresar_movimientos_manuales(self):
        if not self.movimientos_actuales:
            self.agregar_log("No hay movimientos manuales para invertir.")
            return

        self.agregar_log("Invirtiendo movimientos manuales para regresar a la posición inicial...")
        exito = self.robot.ejecutar_secuencia(
            self.movimientos_actuales,
            log_callback=self.agregar_log,
            invertir=True,
        )
        if exito:
            self.agregar_log("Regreso manual completado. El brazo volvió a su posición base.")
            self.movimientos_actuales.clear()

    def quemar_rutina(self):
        if not self.movimientos_actuales:
            self.agregar_log("No hay movimientos manuales para quemar.")
            return

        self.rutina_quemada = [dict(mov) for mov in self.movimientos_actuales]
        self.guardar_rutina_quemada()
        self.agregar_log(f"Rutina quemada con {len(self.rutina_quemada)} movimientos.")

    def ejecutar_rutina_quemada(self):
        if not self.rutina_quemada:
            self.agregar_log("No existe una rutina quemada para ejecutar.")
            return

        self.agregar_log("Ejecutando rutina quemada: ida...")
        exito_ida = self.robot.ejecutar_secuencia(
            self.rutina_quemada,
            log_callback=self.agregar_log,
            invertir=False,
        )
        if not exito_ida:
            return

        self.agregar_log("Ejecutando rutina quemada: regreso invertido...")
        exito_regreso = self.robot.ejecutar_secuencia(
            self.rutina_quemada,
            log_callback=self.agregar_log,
            invertir=True,
        )
        if exito_regreso:
            self.agregar_log("Rutina quemada finalizada. El brazo volvió a la posición base.")

    def limpiar_rutina(self):
        self.movimientos_actuales.clear()
        self.rutina_quemada.clear()
        if self.archivo_rutina.exists():
            self.archivo_rutina.unlink()
        self.agregar_log("Movimientos manuales y rutina quemada borrados.")

    def guardar_rutina_quemada(self):
        payload = {
            "guardado_en": datetime.now().isoformat(),
            "movimientos": self.rutina_quemada,
        }
        with self.archivo_rutina.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def cargar_rutina_quemada(self):
        if not self.archivo_rutina.exists():
            return
        try:
            with self.archivo_rutina.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            self.rutina_quemada = payload.get("movimientos", [])
        except Exception:
            self.rutina_quemada = []

    def rutina_lectura(self):
        respuesta = self.robot.leer_datos()
        if respuesta:
            if "X:" in respuesta and "Count" in respuesta:
                self.procesar_coordenadas(respuesta)

    def procesar_coordenadas(self, texto):
        texto_limpio = texto.split(" Count ")[0]
        partes = texto_limpio.split()

        for parte in partes:
            if parte.startswith("X:"):
                grados = float(parte.replace("X:", ""))
                self.ui.labels_posicion["X"].setText(f"Pos: {grados:.1f}°")
            elif parte.startswith("Y:"):
                grados = float(parte.replace("Y:", ""))
                self.ui.labels_posicion["Y"].setText(f"Pos: {grados:.1f}°")
            elif parte.startswith("Z:"):
                grados = float(parte.replace("Z:", ""))
                self.ui.labels_posicion["Z"].setText(f"Pos: {grados:.1f}°")
            elif parte.startswith("E:"):
                grados = float(parte.replace("E:", ""))
                self.ui.labels_posicion["T"].setText(f"Pos: {grados:.1f}°")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = ControladorPrincipal()
    ventana.show()
    sys.exit(app.exec())
