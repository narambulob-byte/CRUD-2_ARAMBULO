from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


# =====================================================================
# CLASE BASE (ABSTRACTA)
# =====================================================================
# Solo dice QUÉ métodos debe tener todo controlador.
# CÓMO se hace cada uno lo escribe cada controlador, de la forma más simple.
class CrudBase(ABC):

    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass


# =====================================================================
# CONTROLADOR DE ESTUDIANTES
# =====================================================================
class EstudianteController(CrudBase):

    def __init__(self, archivo="data/estudiantes.json"):
        self.gestor = GestorJSON(archivo)

        # Leemos el JSON y convertimos cada diccionario en un objeto 
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Estudiante.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for estudiante in self.lista:
            datos.append(estudiante.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # Al crear hay que traer los tres obligatorios; al actualizar, solo lo que cambia
        # TUPLA: campos obligatorios
        if id_actual is None:
            for campo in ("nombre", "apellido", "email","carnet"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        # Evitar campos obligatorios vacíos al actualizar
        for campo in("nombre","apellido","email","carnet"):
            if campo in datos and str(datos[campo].strip()) == "":
                return f"El campo {campo} no puede estar vacio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            
            # CONJUNTO con los emails de los OTROS clientes ( que sea unico)
            usados = {c.email for c in self.lista if c.id != id_actual}
            if email in usados:
                return "Ese email ya está registrado"

        return None

    def leer(self):
        return self.lista

    def obtener(self, id_estudiante):
        for estudiante in self.lista:
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []

        if texto == "":
            return encontrados

        #TUPLA: campos en los que podemos
        for estudiante in self.lista:
            campos = (
                estudiante.nombre,
                estudiante.apellido,
                estudiante.email,
                estudiante.carnet,
                estudiante.carrera
            )

            for campo in campos:
                if texto in campo.lower():
                    encontrados.append(estudiante)
                    break

        return encontrados

    def siguiente(self):
        mayor = 0
        for estudiante in self.lista:
            if estudiante.id > mayor:
                mayor = estudiante.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        estudiante = Estudiante(
            self.siguiente(),
            str(datos["nombre"]).strip().title(),
            str(datos["apellido"]).strip().title(),
            str(datos["email"]).strip().lower(),
            str(datos["carnet"]).strip().upper(),
            str(datos.get("carrera", "")).strip().title(),
        )

        self.lista.append(estudiante)
        self.guardar()
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, datos):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not datos:
            return False, "No se indicó ningún cambio"

        # DIFERENCIA de conjuntos: campos que no existen 
        permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
        desconocidos = set(datos) - permitidos

        if desconocidos:
            return False, f"Campos no válidos"

        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_estudiante)
        if error:
            return False, error

        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            elif campo == "carnet":
                valor = valor.upper()
            setattr(estudiante, campo, valor)

        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    # --- propio de clientes ---
    def carreras(self):
        #CONJUNTO: Carreras sin repetir
        return sorted({e.carrera for e in self.lista if e.carrera != ""})


# =====================================================================
# CONTROLADOR DE MATERIAS
# =====================================================================
class MateriaController(CrudBase):

    def __init__(self, archivo="data/materias.json"):
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Materia.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for materia in self.lista:
            datos.append(materia.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            for campo in ("nombre", "codigo", "creditos", "cupos"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "nombre" in datos and str(datos["nombre"]).strip() == "":
            return "El nombre no puede estar vacio"

        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            if codigo == "":
                return"El codigo no puede estar vacio"

            #CONJUNTO: codigos unicos
            usados = {m.codigo.upper() for m in self.lista if m.id != id_actual}
            if codigo in usados:
                return "Ese codigo ya esta registrado"

        if "creditos" in datos:
            try:
                creditos = int(datos["creditos"])
                if not 1 <= creditos <= 10:
                    return "Los creditos deben estar entre 1 y 10"
            except (ValueError,TypeError):
                return "Los creditos deben ser numeros enteros"

        if "cupos" in datos:
            try:
                cupos = int(datos["cupos"])
                if not 0 <= cupos <= Materia.CUPOS_MAXIMOS:
                    return "Los cupos deben estar entre 0 y 30"
            except (ValueError, TypeError):
                return "Los cupos deben ser numeros enteros"
                
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_materia):
        for materia in self.lista:
            if materia.id == id_materia:
                return materia
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []

        if texto == "":
            return encontrados

        for materia in self.lista:
            if (texto in materia.nombre.lower()
                or texto in materia.codigo.lower()):
                encontrados.append(materia)
        return encontrados

    def siguiente(self):
        mayor = 0
        for materia in self.lista:
            if materia.id > mayor:
                mayor = materia.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        materia = Materia(
            self.siguiente(),
            str(datos["nombre"]).strip().title(),
            str(datos["codigo"]).strip().upper(),
            int(datos["creditos"]),
            int(datos["cupos"])
        )

        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, datos):
        materia = self.obtener(id_materia)

        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not datos:
            return False, "No se indicó ningún cambio"

        permitidos = {"nombre", "codigo", "creditos", "cupos"}
        desconocidos = set(datos) - permitidos

        if desconocidos:
            return False, "Campos no válidos"

        error = self.validar(datos, id_materia)
        if error:
            return False, error

        for campo, valor in datos.items():
            if campo == "nombre":
                valor = str(valor).strip().title()
            elif campo == "codigo":
                valor = str(valor).strip().upper()
            else:
                valor = int(valor)

            setattr(materia, campo, valor)

        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        materia = self.obtener(id_materia)

        if materia is None:
            return False, f"No existe una materia con id {id_materia}"

        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.lista:
            if not materia.hay_cupo():
                sin_cupo.append(materia)
        return sin_cupo


# =====================================================================
# CONTROLADOR DE MATRICULAS
# =====================================================================
class MatriculaController(CrudBase):

    def __init__(self, estudiantes, materias, archivo="data/matriculas.json"):
        # Hay que pasarle los MISMOS que usa main.py.
        self.estudiantes = estudiantes
        self.materias = materias
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Matricula.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for matricula in self.lista:
            datos.append(matricula.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "Los ID deben ser números enteros"

        periodo = str(datos.get("periodo", "")).strip()
        if not periodo:
            return "El periodo es obligatorio"

        #CONJUNTO: verificar ID de estudiantes
        ids = {e.id for e in self.estudiantes.leer()}
        if self.estudiantes_id not in ids:
            return "El estudiante no existe"

        materia = self.materias.obtener(materia_id)
        if materia is None:
            return "La materia no existe"

        if not materia.hay_cupo():
            return "La materia no tiene cupos disponibles"

        #Evitar matricula duplicada en el mismo periodo
        for matricula in self.lista:
            if (matricula.estudiante_id == estudiante_id
                    and matricula.materia_id == materia_id
                    and matricula.periodo == periodo):
                return "El estudiante ya esta matriculado en esta materia y periodo"   

        return None 
        
    def leer(self):
        return self.lista

    def obtener(self, id_matricula):
        for matricula in self.lista:
            if matricula.id == id_matricula:
                return matricula
        return None

    def buscar(self, texto):
            encontrados = []
            for matricula in self.lista:
                if texto.strip() and texto.strip() in matricula.periodo:
                    encontrados.append(matricula)
            return encontrados

    def siguiente(self):
        mayor = 0
        for matricula in self.lista:
            if matricula.id > mayor:
                mayor = matricula.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        materia = self.materias.obtener(int(datos["materia_id"]))

        matricula = Matricula(
            self.siguiente(),
            int(datos["estudiante_id"]),
            materia.id,
            str(datos["periodo"]).strip()
        )

        materia.ocupar_cupo()
        self.materias.guardar()

        self.lista.append(matricula)
        self.guardar()

        return True, f"Matricula {matricula.id} registrada correctamente"
    
    def actualizar(self, id_matricula, datos):
        return False, "Use registrar_nota() para modificar la nota"

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)

        if matricula is None:
            return False, "La matricula no existe"

        if not Materia.es_nota_valida(nota):
            return False, "La nota debe estar entre 0 y 20"

        matricula.nota = float(nota)
        self.guardar()

        return True, f"Nota registrada. Estado: {matricula.estado()}"
    
    def eliminar(self, id_matricula):
        matricula = self.obtener(id_matricula)

        if matricula is None:
            return False, "La matricula no existe"

        materia = self.materias.obtener(matricula.materia_id)

        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()

        self.lista.remove(matricula)
        self.guardar()

        return True, "Matricula retirada y cupo liberado"

    def retirar_matricula(self, id_matricula):
        return self.eliminar(id_matricula)

    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)

        if matricula is None:
            return None

        #DICCIONARIOS: indices para busacr por ID
        estudiantes = {e.id: e for e in self.estudiantes.leer()}
        materias = {m.id: m for m in self.materias.leer()}

        estudiante = estudiantes.get(matricula.estudiante_id)
        materia = materias.get(matricula.materia_id)

        texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
        texto += f"Estudiante: {estudiante.nombre_completo() if estudiante else 'No encontrado'}\n"
        texto += f"Materia: {materia.nombre if materia else 'No encontrada'}\n"
        texto += "-" * 40 + "\n"
        texto += f"Nota: {matricula.nota if matricula.nota is not None else 'Pendiente'}\n"
        texto += f"Estado: {matricula.estado()}"

        return texto

    def matriculas_por_estudiante(self):
        #DICCIONARIO de LISTAS: agrupar matriculas
        agrupadas = {}
        for matricula in self.lista:
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        notas = []
        for matricula in self.lista:
            if matricula.estudiante_id == id_estudiante and matricula.nota is not None:
                notas.append(matricula.nota)

        if not notas:
            return None

        return round(sum(notas) / len(notas), 2)