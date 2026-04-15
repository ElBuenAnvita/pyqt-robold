import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer

from gui_layout import InterfazBrazoUI
from robot_serial import BrazoRoboticoMarlin

class ControladorPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Brazo 6DOF - Robolds")
        self.setFixedSize(550, 560) # Hicimos la ventana un poquito más alta
        
        self.ui = InterfazBrazoUI()
        self.setCentralWidget(self.ui)
        self.robot = BrazoRoboticoMarlin()
        
        self.timer_serial = QTimer()
        self.timer_serial.timeout.connect(self.rutina_lectura)
        
        # --- NUEVO: Timer exclusivo para la Garra ---
        self.timer_garra = QTimer()
        self.timer_garra.setSingleShot(True) # Hace que solo se ejecute 1 vez y se apague
        self.timer_garra.timeout.connect(self.robot.detener_servo)
        
        self.actualizar_lista_puertos()
        self.conectar_eventos()

    def conectar_eventos(self):
        self.ui.btn_conectar.clicked.connect(self.toggle_conexion)
        self.ui.btn_leer_pos.clicked.connect(self.robot.solicitar_posicion)
        self.ui.btn_fijar_cero.clicked.connect(self.robot.fijar_cero_y_limites)
        self.ui.btn_stop.clicked.connect(self.robot.detener_servo)
        
        self.ui.slider_velocidad.valueChanged.connect(self.al_cambiar_velocidad)
        
        # Conexiones nuevas para la garra
        self.ui.slider_vel_garra.valueChanged.connect(self.al_cambiar_vel_garra)
        self.ui.btn_abrir_garra.clicked.connect(self.abrir_garra)
        self.ui.btn_cerrar_garra.clicked.connect(self.cerrar_garra)
        
        for eje_id, btn in self.ui.botones_mover.items():
            btn.clicked.connect(lambda checked, e=eje_id: self.ejecutar_movimiento(e))

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
            else:
                self.ui.lbl_estado.setText(f"Error: {mensaje}")
        else:
            self.timer_serial.stop()
            self.robot.desconectar()
            self.ui.lbl_estado.setText("Desconectado")
            self.ui.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
            self.ui.btn_conectar.setText("Conectar")

    def al_cambiar_velocidad(self):
        valor = self.ui.slider_velocidad.value()
        self.ui.lbl_velocidad_val.setText(f"{valor}%")
        self.robot.cambiar_velocidad(valor)

    # --- LÓGICA DE LA GARRA ---
    def al_cambiar_vel_garra(self):
        valor = self.ui.slider_vel_garra.value()
        self.ui.lbl_vel_garra_val.setText(f"{valor}%")

    def abrir_garra(self):
        """Mapea el porcentaje de 10-100% a valores de PWM de 81 a 0 (Apertura)"""
        velocidad_pct = self.ui.slider_vel_garra.value()
        valor_pwm = int(90 - (velocidad_pct * 0.9))
        self.robot.mover_eje("Servo", valor_pwm)
        
        # Iniciamos el contador de 3 segundos (3000 ms) para detenerlo
        self.timer_garra.start(3000)

    def cerrar_garra(self):
        """Mapea el porcentaje de 10-100% a valores de PWM de 99 a 180 (Cierre)"""
        velocidad_pct = self.ui.slider_vel_garra.value()
        valor_pwm = int(90 + (velocidad_pct * 0.9))
        self.robot.mover_eje("Servo", valor_pwm)
        
        # Iniciamos el contador de 3 segundos (3000 ms) para detenerlo
        self.timer_garra.start(3000)
    # -------------------------

    def ejecutar_movimiento(self, eje_id):
        try:
            texto_ingresado = self.ui.inputs[eje_id].text()
            grados = float(texto_ingresado)
            self.robot.mover_eje(eje_id, grados)
        except ValueError:
            print("Por favor ingrese un valor numérico válido.")

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