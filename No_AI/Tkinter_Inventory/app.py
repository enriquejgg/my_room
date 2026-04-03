from tkinter import ttk
from tkinter import *
import tkinter as tk
import sqlite3


class Producto:

    db = 'database/productos.db'

    def __init__(self, root):
        self.ventana = root
        self.ventana.title("App Gestor de Produtos")
        # Titulo de la ventana
        self.ventana.resizable(1, 1)
        # Activar la redimension de la ventana.
        # Para desactivarla: (0, 0)
        self.ventana.wm_iconbitmap('resources/gear.ico')

        # Creacion del contenedor Frame principal
        frame = LabelFrame(self.ventana, text="Registrar un nuevo Producto", font=('Calibri', 16, 'bold'), bg="#FF9966")
        frame.grid(row=0, column=0, columnspan=3, pady=20)


###################### LABELS ####################

        # Label Nombre
        self.etiqueta_nombre = Label(frame, text="Nombre: ", font=('Calibri', 13), bg="#CCFF99")  # Etiqueta de texto ubicada en el frame
        self.etiqueta_nombre.grid(row=1, column=0, sticky=W)  # Posicionamiento a traves de grid
        # Entry Nombre (caja de texto que recibira el nombre)
        self.nombre = Entry(frame, font=('Calibri', 13))
        # Caja de texto (input de texto) ubicada en el frame
        self.nombre.focus()
        # Para que el foco del raton vaya a este Entry al inicio
        self.nombre.insert(0, '')
        # self.nombre.configure(state=DISABLED)
        self.nombre.grid(row=1, column=1)

        # Label Precio
        self.etiqueta_precio = Label(frame, text="Precio: ", font=('Calibri', 13), bg="#CCFF99")  # Etiqueta de texto ubicada en el frame
        self.etiqueta_precio.grid(row=2, column=0, sticky=W)
        # Entry Precio (caja de texto que recibira el precio)
        self.precio = Entry(frame, font=('Calibri', 13))  # Caja de texto (input de texto) ubicada en el frame
        self.precio.insert(0, '')
        self.precio.grid(row=2, column=1)

        # Label Stock
        self.etiqueta_stock = Label(frame, text="Stock: ",
                                     font=('Calibri', 13), bg="#CCFF99")  # Etiqueta de texto ubicada en el frame
        self.etiqueta_stock.grid(row=3, column=0, sticky=W)
        # Entry Stock (caja de texto que recibira el stock)
        self.stock = Entry(frame, font=('Calibri', 13))  # Caja de texto (input de texto) ubicada en el frame
        self.stock.insert(0, 0)
        self.stock.grid(row=3, column=1)

        # Label Combo title

        self.combo = Label(frame, text="Categoria :",
                  font=('Calibri', 13), bg="#CCFF99").grid(column=0, row=4)

        n = tk.StringVar()
        self.categoria = ttk.Combobox(frame, width=27, textvariable=n)
        self.categoria['values'] = ('Informatica',
                                  'Telefonia',
                                  'Hogar',
                                  'Imagen y Sonido',
                                  'Otras')

        self.categoria.grid(column=1, row=4, sticky=W)

###################### INFO MESSAGE & ADD BUTTON ####################

        # Mensaje informativo para el usuario
        self.mensaje = Label(text='', fg='red')
        self.mensaje.grid(row=6, column=0, columnspan=2, sticky=W + E) ########

        # Boton Añadir Producto
        s = ttk.Style()
        s.configure('my.TButton', font=('Calibri', 14, 'bold'))
        self.boton_aniadir = ttk.Button(frame, text="Guardar Producto", command=self.add_producto, style='my.TButton')
        self.boton_aniadir.grid(row=5, columnspan=2, sticky=W + E) ########

###################### TABLE ####################

        # Tabla de Productos
        # Estilo personalizado para la tabla
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Calibri', 11))
        # Se modifica la fuente de la tabla
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))
        # Se modifica la fuente de las cabeceras
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        # Eliminamos los bordes

        # Estructura de la tabla
        self.tabla = ttk.Treeview(height=20, columns = ('Nombre', 'Precio', 'Stock', 'Categoria'), style="mystyle.Treeview") ########
        self.tabla.grid(row=5, column=0, columnspan=2)
        self.tabla.heading('#0', text='Nombre', anchor=CENTER)  # Encabezado 0
        self.tabla.heading('#1', text='Precio', anchor=CENTER)  # Encabezado 1
        self.tabla.heading('#2', text='Stock', anchor=CENTER)  # Encabezado 2
        self.tabla.heading('#3', text='Categoria', anchor=CENTER)  # Encabezado 3

###################### BUTTONS DELETE EDIT ####################

        # Botones de Eliminar y Editar
        s = ttk.Style()
        s.configure('my.TButton', font=('Calibri', 14, 'bold'))
        boton_eliminar = ttk.Button(text='ELIMINAR', command=self.del_producto, style='my.TButton')
        boton_eliminar.grid(row=9, column=0, sticky=W + E)
        boton_editar = ttk.Button(text='EDITAR', command=self.edit_producto, style='my.TButton')
        boton_editar.grid(row=9, column=1, sticky=W + E)

        self.get_productos()

###################### FUNCTION LOOK UP ####################

    def db_consulta(self, consulta, parametros=()):
        with sqlite3.connect(self.db) as con:
            # Iniciamos una conexion con la base de datos(alias con)
            cursor = con.cursor()
            # Generamos un cursor de la conexion para poder operar en la base de datos
            resultado = cursor.execute(consulta, parametros)
            # Preparar la consulta SQL(con parametros si los hay)
            con.commit()  # Ejecutar la consulta SQL preparada anteriormente
        return resultado  # Retornar el resultado de la consulta SQL

###################### FUNCTION DISPLAY ####################

    def get_productos(self):
        # Lo primero, al iniciar la app, vamos a limpiar la tabla por si hubiera datos residuales o antiguos
        registros_tabla = self.tabla.get_children()  # Obtener todos los datos de la tabla
        for fila in registros_tabla:
            self.tabla.delete(fila)

        query = 'SELECT * FROM producto ORDER BY nombre ASC'
        registros_db = self.db_consulta(query)
        # Se hace la llamada al metodo db_consultas
        # print(registros)  # Se muestran los resultados
        # Llamada al metodo get_productos() para obtener el listado de productos al inicio de la app

        # Escribir los datos en pantalla
        for fila in registros_db:
            print(fila)  # print para verificar por consola los datos
            self.tabla.insert('', 0, text=fila[1], values=(fila[2], fila[3], fila[4]))

###################### FUNCTION VALIDATION ####################

    def validacion_nombre(self):
        nombre_introducido_por_usuario = self.nombre.get()
        return len(nombre_introducido_por_usuario) != 0

    def validacion_precio(self):
        precio_introducido_por_usuario = self.precio.get()
        return len(precio_introducido_por_usuario) != 0

    def validacion_stock(self):
        stock_introducido_por_usuario = self.stock.get()
        return len(stock_introducido_por_usuario) != 0

    def validacion_categoria(self):
        categoria_introducida_por_usuario = self.categoria.get()
        return len(categoria_introducida_por_usuario) != 0

###################### FUNCTION ADD ####################

    def add_producto(self):
        if self.validacion_nombre() and self.validacion_precio() and self.validacion_stock() and self.validacion_categoria:
            query = 'INSERT INTO producto VALUES(NULL, ?, ?, ?, ?)'  # Consulta SQL (sin los datos), to send nothing we use NULL
            parametros = (self.nombre.get(), self.precio.get(), self.stock.get(), self.categoria.get())  # Parametros de la consulta SQL
            self.db_consulta(query, parametros)
            print("Datos guardados")
            self.mensaje['text'] = 'Producto {} añadido con éxito'.format(self.nombre.get())
            # Label ubicado entre el boton y la tabla
            self.nombre.delete(0, END)  # Borrar el campo nombre del formulario
            self.precio.delete(0, END)  # Borrar el campo precio del formulario
            self.stock.delete(0, END)  # Borrar el campo stock del formulario
            self.categoria.delete(0, END)
# print("Datos guardados")
# print(self.nombre.get())
# print(self.precio.get())
        elif self.validacion_nombre() and self.validacion_precio() == False and self.validacion_categoria():
            # print("El precio es obligatorio")
            self.mensaje['text'] = 'El precio es obligatorio'
        elif self.validacion_nombre() == False and self.validacion_precio() and self.validacion_categoria():
            # print("El nombre es obligatorio")
            self.mensaje['text'] = 'El nombre es obligatorio'
        elif self.validacion_nombre() and self.validacion_precio() and self.validacion_categoria() == False:
            # print("El nombre es obligatorio")
            self.mensaje['text'] = 'La categoria es obligatoria'
        elif self.validacion_nombre() and self.validacion_precio() == False and self.validacion_categoria() == False:
            # print("El nombre es obligatorio")
            self.mensaje['text'] = 'La categoria y el precio son obligatorios'
        elif self.validacion_nombre() == False and self.validacion_precio() and self.validacion_categoria() == False:
            # print("El nombre es obligatorio")
            self.mensaje['text'] = 'El nombre y la categoria son obligatorios'
        elif self.validacion_nombre() == False and self.validacion_precio() == False and self.validacion_categoria():
            # print("El nombre es obligatorio")
            self.mensaje['text'] = 'El nombre y el precio son obligatorios'
        else:
            # print("El nombre y el precio son obligatorios")
            self.mensaje['text'] = 'El nombre, precio y categoria son obligatorios'

        self.get_productos()
        # Cuando se finalice la insercion de datos volvemos a
        # invocar a este metodo para actualizar el contenido y ver los cambios

###################### FUNCTION DELETE ####################

    def del_producto(self):
        print(self.tabla.item(self.tabla.selection()))

        self.mensaje['text'] = ''  # Mensaje inicialmente vacio
        # Comprobacion de que se seleccione un producto para poder eliminarlo
        try:
            self.tabla.item(self.tabla.selection())['text'][0]
        except IndexError as e:
            self.mensaje['text'] = 'Por favor, seleccione un producto'
            return
        self.mensaje['text'] = ''
        nombre = self.tabla.item(self.tabla.selection())['text']
        query = 'DELETE FROM producto WHERE nombre = ?'  # Consulta SQL
        self.db_consulta(query, (nombre,)) # Ejecutar la consulta
        self.mensaje['text'] = 'Producto {} eliminado con éxito'.format(nombre)
        self.get_productos() # Actualizar la tabla de productos

###################### FUNCTION EDIT ####################

    def edit_producto(self):
        self.mensaje['text'] = ''  # Mensaje inicialmente vacio
        try:
            self.tabla.item(self.tabla.selection())['text'][0]
        except IndexError as e:
            self.mensaje['text'] = 'Por favor, seleccione un producto'
            return
        nombre = self.tabla.item(self.tabla.selection())['text']
        old_precio = self.tabla.item(self.tabla.selection())['values'][0]  # El precio se encuentra dentro de una lista
        old_stock = self.tabla.item(self.tabla.selection())['values'][1]
        old_category = self.tabla.item(self.tabla.selection())['values'][2]

        self.ventana_editar = Toplevel()  # Crear una ventana por delante de la principal, secundaria
        self.ventana_editar.title = "Editar Producto"  # Titulo de la ventana
        self.ventana_editar.resizable(1, 1)  # Activar la redimension de la ventana. Para desactivarla: (0,0)
        self.ventana_editar.wm_iconbitmap('recursos/gear.ico')  # Icono de la ventana

        titulo = Label(self.ventana_editar, text='Edición de Productos', font=('Calibri', 50, 'bold'))
        titulo.grid(column=0, row=0)
        # Creacion del contenedor Frame de la ventana de Editar Producto
        frame_ep = LabelFrame(self.ventana_editar, text="Editar el siguiente Producto", font=('Calibri', 16, 'bold'))
        # frame_ep: Frame Editar Producto
        frame_ep.grid(row=1, column=0, columnspan=20, pady=20)

#####################

        # Label Nombre antiguo
        self.etiqueta_nombre_anituguo = Label(frame_ep, text="Nombre antiguo: ", font=('Calibri', 13))
        # Etiqueta de texto ubicada en el frame
        self.etiqueta_nombre_anituguo.grid(row=2, column=0)
        # Posicionamiento a traves de grid

        # Entry Nombre antiguo (texto que no se podra modificar)
        self.input_nombre_antiguo = Entry(frame_ep, textvariable=StringVar(self.ventana_editar, value=nombre), state='readonly', font=('Calibri', 13))
        self.input_nombre_antiguo.grid(row=2, column=1)


        # Label Nombre nuevo
        self.etiqueta_nombre_nuevo = Label(frame_ep, text="Nombre nuevo: ", font=('Calibri', 13))
        self.etiqueta_nombre_nuevo.grid(row=3, column=0)

        # Entry Nombre nuevo (texto que si se podra modificar)
        self.input_nombre_nuevo = Entry(frame_ep, font=('Calibri', 13))
        self.input_nombre_nuevo.grid(row=3, column=1)
        self.input_nombre_nuevo.focus()  # Para que el foco del raton vaya a este Entry al inicio

######################

        # Label Precio antiguo
        self.etiqueta_precio_anituguo = Label(frame_ep, text="Precio antiguo: ", font=('Calibri', 13))
        # Etiqueta de texto ubicada en el frame
        self.etiqueta_precio_anituguo.grid(row=4, column=0) # Posicionamiento a traves de grid
        # Entry Precio antiguo (texto que no se podra modificar)
        self.input_precio_antiguo = Entry(frame_ep, textvariable=StringVar(self.ventana_editar, value=old_precio),
                                          state='readonly', font=('Calibri', 13))
        self.input_precio_antiguo.grid(row=4, column=1)


        # Label Precio nuevo
        self.etiqueta_precio_nuevo = Label(frame_ep, text="Precio nuevo: ", font=('Calibri', 13))
        self.etiqueta_precio_nuevo.grid(row=5, column=0)
        # Entry Precio nuevo (texto que si se podra modificar)
        self.input_precio_nuevo = Entry(frame_ep, font=('Calibri', 13))
        self.input_precio_nuevo.grid(row=5, column=1)

#######################

        # Label Stock antiguo
        self.etiqueta_old_stock = Label(frame_ep, text="Stock antiguo: ", font=('Calibri', 13))
        # Etiqueta de texto ubicada en el frame
        self.etiqueta_old_stock.grid(row=6, column=0)
        # Posicionamiento a traves de grid

        # Entry Stock antiguo (texto que no se podra modificar)
        self.input_old_stock = Entry(frame_ep, textvariable=StringVar(self.ventana_editar, value=old_stock),
                                     state='readonly', font=('Calibri', 13))
        self.input_old_stock.grid(row=6, column=1)

        # Label Stock nuevo
        self.etiqueta_new_stock = Label(frame_ep, text="Stock nuevo: ", font=('Calibri', 13))
        self.etiqueta_new_stock.grid(row=7, column=0)
        # Entry Stock nuevo (texto que si se podra modificar)
        self.input_new_stock = Entry(frame_ep, font=('Calibri', 13))
        self.input_new_stock.grid(row=7, column=1)

#######################

        # Label Categoria Antigua
        self.etiqueta_categoria_antigua = Label(frame_ep, text="Categoria antigua: ", font=('Calibri', 13))
        # Etiqueta de texto ubicada en el frame
        self.etiqueta_categoria_antigua.grid(row=8, column=0)
        # Posicionamiento a traves de grid

        # Entry Categoria antigua (texto que no se podra modificar)
        self.input_old_category = Entry(frame_ep, textvariable=StringVar(self.ventana_editar, value=old_category),
                                     state='readonly', font=('Calibri', 13))
        self.input_old_category.grid(row=8, column=1)

        # Label Categoria Nueva
        self.combo = Label(frame_ep, text="Categoria nueva :",
                           font=('Calibri', 13)).grid(column=0, row=9)

        # Entry Categoria nueva
        k = tk.StringVar()
        self.input_category_new = ttk.Combobox(frame_ep, width=20, textvariable=k)
        self.input_category_new['values'] = ('Informatica',
                                    'Telefonia',
                                    'Hogar',
                                    'Imagen y Sonido',
                                    'Otras')

        self.input_category_new.grid(column=1, row=9)

        # Boton Actualizar Producto
        s = ttk.Style()
        s.configure('my.TButton', font=('Calibri', 14, 'bold'))
        self.boton_actualizar = ttk.Button(frame_ep, text="Actualizar Producto", style='my.TButton', command=lambda:
        self.actualizar_productos(self.input_nombre_nuevo.get(),
        self.input_nombre_antiguo.get(),
        self.input_precio_nuevo.get(),
        self.input_precio_antiguo.get(),
        self.input_new_stock.get(),
        self.input_old_stock.get(),
        self.input_category_new.get(),
        self.input_old_category.get()))

        self.boton_actualizar.grid(row=10, columnspan=2, sticky=W + E)

###################### FUNCTION UPDATE ####################

    def actualizar_productos(self, nuevo_nombre, antiguo_nombre, nuevo_precio, antiguo_precio, nuevo_stock, antiguo_stock, new_category, old_category):

        producto_modificado = False
        query = 'UPDATE producto SET nombre = ?, precio = ?, stock = ?, categoria = ? WHERE nombre = ? AND precio = ? AND stock = ? AND categoria = ?'

        if nuevo_nombre != '' and nuevo_precio != '' and nuevo_stock != '' and new_category != '':
            # Si el usuario escribe nuevo nombre y nuevo precio, se cambian ambos
            parametros = (nuevo_nombre, nuevo_precio, nuevo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre != '' and nuevo_precio == '' and nuevo_stock == '' and new_category == '':
            # Si el usuario deja vacio el nuevo precio,
            parametros = (nuevo_nombre, antiguo_precio, antiguo_stock, old_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio != '' and nuevo_stock == '' and new_category == '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (antiguo_nombre, nuevo_precio, antiguo_stock, old_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio == '' and nuevo_stock != '' and new_category == '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (antiguo_nombre, antiguo_precio, nuevo_stock, old_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio != '' and nuevo_stock != '' and new_category == '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (antiguo_nombre, nuevo_precio, nuevo_stock, old_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre != '' and nuevo_precio == '' and nuevo_stock != '' and new_category == '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (nuevo_nombre, antiguo_precio, nuevo_stock, old_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre != '' and nuevo_precio != '' and nuevo_stock == '' and new_category == '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (nuevo_nombre, nuevo_precio, antiguo_stock, old_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio == '' and nuevo_stock == '' and new_category != '':
            # Si el usuario deja vacio el nuevo precio,
            parametros = (antiguo_nombre, antiguo_precio, antiguo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre != '' and nuevo_precio == '' and nuevo_stock == '' and new_category != '':
            # Si el usuario deja vacio el nuevo precio,
            parametros = (nuevo_nombre, antiguo_precio, antiguo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio != '' and nuevo_stock == '' and new_category != '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (antiguo_nombre, nuevo_precio, antiguo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio == '' and nuevo_stock != '' and new_category != '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (antiguo_nombre, antiguo_precio, nuevo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre == '' and nuevo_precio != '' and nuevo_stock != '' and new_category != '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (antiguo_nombre, nuevo_precio, nuevo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre != '' and nuevo_precio == '' and nuevo_stock != '' and new_category != '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (nuevo_nombre, antiguo_precio, nuevo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True
        elif nuevo_nombre != '' and nuevo_precio != '' and nuevo_stock == '' and new_category != '':
            # Si el usuario deja vacio el nuevo nombre, anterior
            parametros = (nuevo_nombre, nuevo_precio, antiguo_stock, new_category, antiguo_nombre, antiguo_precio, antiguo_stock, old_category)
            producto_modificado = True

        if (producto_modificado):
            self.db_consulta(query, parametros)  # Ejecutar la consulta
            self.ventana_editar.destroy()  # Cerrar la ventana de edicion de productos
            self.mensaje['text'] = 'El producto {} ha sido actualizado con éxito'.format(antiguo_nombre)
            # Mostrar mensaje para el usuario
            self.get_productos()  # Actualizar la tabla de productos
        else:
            self.ventana_editar.destroy()
            # Cerrar la ventana de edicion de productos
            self.mensaje['text'] = 'El producto {} NO ha sido actualizado'.format(antiguo_nombre)
            # Mostrar mensaje para el usuario
        self.get_productos()  # Actualizar la tabla de productos


if __name__ == '__main__':
    root = Tk()  # Instancia de la ventana principal
    app = Producto(root)  # Se envia a la clase Producto el control sobre la ventana root
    root.mainloop()  # Comenzamos el bucle de aplicacion, es como un while True

# https://www.delftstack.com/howto/python-tkinter/how-to-create-dropdown-menu-in-tkinter/