import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer

# Importamos nuestros módulos recién creados
from gui_layout import InterfazBrazoUI
from robot_serial import BrazoRoboticoMarlin

class ControladorPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Brazo 6DOF - Robolds")
        self.setFixedSize(550, 480)
        
        # 1. Instanciar la Interfaz (Frontend) y el Hardware (Backend)
        self.ui = InterfazBrazoUI()
        self.setCentralWidget(self.ui)
        self.robot = BrazoRoboticoMarlin()
        
        # 2. Configurar el Reloj para lectura en segundo plano
        self.timer_serial = QTimer()
        self.timer_serial.timeout.connect(self.rutina_lectura)
        
        # 3. Llenar la lista de puertos y conectar eventos
        self.actualizar_lista_puertos()
        self.conectar_eventos()

    def conectar_eventos(self):
        """Conecta los clics de la UI con las acciones del Robot"""
        self.ui.btn_conectar.clicked.connect(self.toggle_conexion)
        self.ui.btn_leer_pos.clicked.connect(self.robot.solicitar_posicion)
        self.ui.btn_fijar_cero.clicked.connect(self.robot.fijar_cero_y_limites)
        self.ui.btn_stop.clicked.connect(self.robot.detener_servo)
        
        self.ui.slider_velocidad.valueChanged.connect(self.al_cambiar_velocidad)
        
        # Conectar cada uno de los botones de Mover Eje
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
                self.timer_serial.start(100) # Iniciar lectura de telemetría
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

    def ejecutar_movimiento(self, eje_id):
        try:
            # Leemos el texto de la UI, lo volvemos número y lo enviamos al Backend
            texto_ingresado = self.ui.inputs[eje_id].text()
            grados = float(texto_ingresado)
            self.robot.mover_eje(eje_id, grados)
        except ValueError:
            print("Por favor ingrese un valor numérico válido.")

    def rutina_lectura(self):
        """Revisa constantemente si el robot nos envió coordenadas"""
        respuesta = self.robot.leer_datos()
        if respuesta:
            print(f"Marlin dice: {respuesta}")
            if "X:" in respuesta and "Count" in respuesta:
                self.procesar_coordenadas(respuesta)

    def procesar_coordenadas(self, texto):
        """Traduce la respuesta de Marlin y actualiza los Labels azules de la UI"""
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