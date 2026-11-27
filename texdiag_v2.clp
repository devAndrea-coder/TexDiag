;;; ============================================================
;;; TexDiag v2 - Sistema experto con factores de certeza (FC)
;;; y preguntas de seguimiento.
;;; Maquina de coser recta industrial
;;; ============================================================

;;; ---------- PARAMETRO ----------
;;; Un diagnostico solo genera tratamiento si su FC alcanza este umbral.
(defglobal ?*UMBRAL* = 0.30)

;;; ---------- PLANTILLAS (estructura de los hechos) ----------

(deftemplate sintoma
   (slot codigo (type SYMBOL))
   (slot nombre (type STRING) (default "")))

(deftemplate respuesta
   (slot pregunta (type SYMBOL))
   (slot valor (type SYMBOL) (allowed-symbols si no nosabe)))

(deftemplate pregunta
   (slot id (type SYMBOL))
   (slot diagnostico (type SYMBOL))
   (slot texto (type STRING)))

(deftemplate evidencia
   (slot diagnostico (type SYMBOL))
   (slot regla (type SYMBOL))
   (slot cf (type NUMBER))
   (slot nota (type STRING) (default "")))

(deftemplate diagnostico
   (slot codigo (type SYMBOL))
   (slot nombre (type STRING))
   (slot cf (type NUMBER))
   (multislot reglas)
   (multislot notas))

(deftemplate tratamiento
   (slot codigo (type SYMBOL))
   (slot nombre (type STRING))
   (slot accion (type STRING))
   (slot regla (type SYMBOL))
   (slot cf (type NUMBER)))

;;; ---------- CATALOGO DE PREGUNTAS DE SEGUIMIENTO ----------

(deffacts catalogo-preguntas
   (pregunta (id P1) (diagnostico D1) (texto "La aguja lleva mas de una semana de uso?"))
   (pregunta (id P2) (diagnostico D1) (texto "La tela es elastica?"))
   (pregunta (id P3) (diagnostico D6) (texto "El ruido continua al girar la maquina sin tela?"))
   (pregunta (id P4) (diagnostico D3) (texto "Se enhebro la maquina hace poco?")))

;;; ---------- FUNCION AUXILIAR ----------

(deffunction nombre-diag (?d)
   (switch ?d
      (case D1 then "Aguja defectuosa")
      (case D2 then "Tension incorrecta")
      (case D3 then "Enhebrado erroneo")
      (case D4 then "Exceso de aceite")
      (case D5 then "Presion o avance mal regulado")
      (case D6 then "Mecanismo desajustado")
      (default "Desconocido")))

;;; ---------- R1-R11: SINTOMA -> EVIDENCIA DE DIAGNOSTICO ----------

(defrule R1-puntada-saltada-aguja
   (sintoma (codigo S1))
   =>
   (assert (evidencia (diagnostico D1) (regla R1) (cf 0.40)))
   (printout t "[R1] S1 => D1 Aguja defectuosa (FC 0.40)" crlf))

(defrule R2-puntada-saltada-mecanismo
   (sintoma (codigo S1))
   =>
   (assert (evidencia (diagnostico D6) (regla R2) (cf 0.30)))
   (printout t "[R2] S1 => D6 Mecanismo desajustado (FC 0.30)" crlf))

(defrule R3-hilo-roto-tension
   (sintoma (codigo S2))
   =>
   (assert (evidencia (diagnostico D2) (regla R3) (cf 0.35)))
   (printout t "[R3] S2 => D2 Tension incorrecta (FC 0.35)" crlf))

(defrule R4-hilo-roto-enhebrado
   (sintoma (codigo S2))
   =>
   (assert (evidencia (diagnostico D3) (regla R4) (cf 0.35)))
   (printout t "[R4] S2 => D3 Enhebrado erroneo (FC 0.35)" crlf))

(defrule R5-lazadas-tension
   (sintoma (codigo S3))
   =>
   (assert (evidencia (diagnostico D2) (regla R5) (cf 0.60)))
   (printout t "[R5] S3 => D2 Tension incorrecta (FC 0.60)" crlf))

(defrule R6-tela-fruncida-presion
   (sintoma (codigo S4))
   =>
   (assert (evidencia (diagnostico D5) (regla R6) (cf 0.60)))
   (printout t "[R6] S4 => D5 Presion o avance mal regulado (FC 0.60)" crlf))

(defrule R7-hilo-deshilachado-aguja
   (sintoma (codigo S5))
   =>
   (assert (evidencia (diagnostico D1) (regla R7) (cf 0.50)))
   (printout t "[R7] S5 => D1 Aguja defectuosa (FC 0.50)" crlf))

(defrule R8-manchas-aceite
   (sintoma (codigo S6))
   =>
   (assert (evidencia (diagnostico D4) (regla R8) (cf 0.90)))
   (printout t "[R8] S6 => D4 Exceso de aceite (FC 0.90)" crlf))

(defrule R9-ruido-mecanismo
   (sintoma (codigo S7))
   =>
   (assert (evidencia (diagnostico D6) (regla R9) (cf 0.55)))
   (printout t "[R9] S7 => D6 Mecanismo desajustado (FC 0.55)" crlf))

(defrule R10-puntada-irregular-enhebrado
   (sintoma (codigo S8))
   =>
   (assert (evidencia (diagnostico D3) (regla R10) (cf 0.40)))
   (printout t "[R10] S8 => D3 Enhebrado erroneo (FC 0.40)" crlf))

(defrule R11-puntada-irregular-presion
   (sintoma (codigo S8))
   =>
   (assert (evidencia (diagnostico D5) (regla R11) (cf 0.30)))
   (printout t "[R11] S8 => D5 Presion o avance mal regulado (FC 0.30)" crlf))

;;; ---------- R12-R15: REFINAMIENTO (respuesta Si + diagnostico previo) ----------

(defrule R12-aguja-uso-prolongado
   (respuesta (pregunta P1) (valor si))
   (exists (evidencia (diagnostico D1)))
   =>
   (assert (evidencia (diagnostico D1) (regla R12) (cf 0.30)))
   (printout t "[R12] P1=si + D1 => refuerza Aguja defectuosa (FC 0.30)" crlf))

(defrule R13-tela-elastica-aguja
   (respuesta (pregunta P2) (valor si))
   (exists (evidencia (diagnostico D1)))
   =>
   (assert (evidencia (diagnostico D1) (regla R13) (cf 0.30)
                      (nota "Tela elastica: usar aguja de punta bola.")))
   (printout t "[R13] P2=si + D1 => refuerza Aguja defectuosa (FC 0.30)" crlf))

(defrule R14-ruido-sin-tela-mecanismo
   (respuesta (pregunta P3) (valor si))
   (exists (evidencia (diagnostico D6)))
   =>
   (assert (evidencia (diagnostico D6) (regla R14) (cf 0.30)))
   (printout t "[R14] P3=si + D6 => refuerza Mecanismo desajustado (FC 0.30)" crlf))

(defrule R15-enhebrado-reciente
   (respuesta (pregunta P4) (valor si))
   (exists (evidencia (diagnostico D3)))
   =>
   (assert (evidencia (diagnostico D3) (regla R15) (cf 0.30)))
   (printout t "[R15] P4=si + D3 => refuerza Enhebrado erroneo (FC 0.30)" crlf))

;;; ---------- REGLA DE CONTROL: COMBINAR EVIDENCIAS ----------
;;; FC = FC1 + FC2 * (1 - FC1), aplicado a todas las evidencias del diagnostico.
;;; Se ejecuta despues de las reglas anteriores (salience menor).

(defrule consolidar-evidencia
   (declare (salience -10))
   (evidencia (diagnostico ?d))
   (not (diagnostico (codigo ?d)))
   =>
   (bind ?cf 0.0)
   (bind ?reglas (create$))
   (bind ?notas (create$))
   (do-for-all-facts ((?e evidencia)) (eq ?e:diagnostico ?d)
      (bind ?cf (+ ?cf (* ?e:cf (- 1.0 ?cf))))
      (bind ?reglas (create$ ?reglas ?e:regla))
      (if (neq ?e:nota "") then (bind ?notas (create$ ?notas ?e:nota))))
   (assert (diagnostico (codigo ?d) (nombre (nombre-diag ?d))
                        (cf ?cf) (reglas ?reglas) (notas ?notas)))
   (printout t "[FC] " ?d " " (nombre-diag ?d) " = " (format nil "%.2f" ?cf) crlf))

;;; ---------- R16-R21: DIAGNOSTICO (FC >= UMBRAL) -> TRATAMIENTO ----------

(defrule R16-cambiar-la-aguja
   (diagnostico (codigo D1) (cf ?cf&:(>= ?cf ?*UMBRAL*)))
   =>
   (assert (tratamiento (codigo T1) (nombre "Cambiar la aguja")
      (accion "Usar el calibre adecuado al grosor de la tela y verificar que quede bien insertada.")
      (regla R16) (cf ?cf)))
   (printout t "[R16] D1 => T1 Cambiar la aguja (FC " (format nil "%.2f" ?cf) ")" crlf))

(defrule R17-ajustar-la-tension
   (diagnostico (codigo D2) (cf ?cf&:(>= ?cf ?*UMBRAL*)))
   =>
   (assert (tratamiento (codigo T2) (nombre "Ajustar la tension")
      (accion "Regular el disco de tension del hilo superior y revisar la tension de la bobina.")
      (regla R17) (cf ?cf)))
   (printout t "[R17] D2 => T2 Ajustar la tension (FC " (format nil "%.2f" ?cf) ")" crlf))

(defrule R18-reenhebrar-el-hilo
   (diagnostico (codigo D3) (cf ?cf&:(>= ?cf ?*UMBRAL*)))
   =>
   (assert (tratamiento (codigo T3) (nombre "Reenhebrar el hilo")
      (accion "Subir el prensatelas y seguir la ruta completa de guias hasta la aguja.")
      (regla R18) (cf ?cf)))
   (printout t "[R18] D3 => T3 Reenhebrar el hilo (FC " (format nil "%.2f" ?cf) ")" crlf))

(defrule R19-limpiar-el-aceite
   (diagnostico (codigo D4) (cf ?cf&:(>= ?cf ?*UMBRAL*)))
   =>
   (assert (tratamiento (codigo T4) (nombre "Limpiar el aceite")
      (accion "Retirar el exceso, limpiar la zona y reducir la cantidad de lubricante.")
      (regla R19) (cf ?cf)))
   (printout t "[R19] D4 => T4 Limpiar el aceite (FC " (format nil "%.2f" ?cf) ")" crlf))

(defrule R20-regular-el-prensatelas
   (diagnostico (codigo D5) (cf ?cf&:(>= ?cf ?*UMBRAL*)))
   =>
   (assert (tratamiento (codigo T5) (nombre "Regular el prensatelas")
      (accion "Ajustar la presion y la altura de los dientes de arrastre segun la tela.")
      (regla R20) (cf ?cf)))
   (printout t "[R20] D5 => T5 Regular el prensatelas (FC " (format nil "%.2f" ?cf) ")" crlf))

(defrule R21-llamar-a-mantenimiento
   (diagnostico (codigo D6) (cf ?cf&:(>= ?cf ?*UMBRAL*)))
   =>
   (assert (tratamiento (codigo T6) (nombre "Llamar a mantenimiento")
      (accion "La sincronizacion del garfio requiere personal tecnico.")
      (regla R21) (cf ?cf)))
   (printout t "[R21] D6 => T6 Llamar a mantenimiento (FC " (format nil "%.2f" ?cf) ")" crlf))
