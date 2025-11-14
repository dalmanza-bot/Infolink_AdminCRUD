from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from supabase import create_client, Client

SUPABASE_URL = "https://exxahnckimfjvxfdhkrz.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4eGFobmNraW1manZ4ZmRoa3J6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTc1MjQ3MSwiZXhwIjoyMDc3MzI4NDcxfQ.hbO1OD5ikj7vx5bQfFrGDNYk_imG0KAuU6hIl2MUSqk" 

# Inicializar Flask
app = Flask(__name__)

# Inicializar Cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read
@app.route("/")
def index():
    try:        
        response = supabase.table("Infolink_Staff").select("*").execute()        
        data = response.data 
        return render_template("index.html", records=data)

    except Exception as e:
        return f"<h1>Error de Conexión o Base de Datos</h1><p>Detalle: {e}</p>", 500
    
# Create
@app.route("/new", methods=["GET"])
def show_create_form():
    return render_template("create.html")

@app.route("/new", methods=["POST"])
def create_record():
    try:        
        new_data = {
            "Employee_ID": request.form.get("id"),
            "FULL NAME": request.form.get("full_name"),
            "ACCOUNT": request.form.get("account"),
            "POSITION": request.form.get("position"),
            "DATE OF ADMISSION": request.form.get("date_of_admition"),
            "PHONE": request.form.get("phone"),
            "CELLPHONE": request.form.get("cellphone"),
            "EMERGENCY NUMBER": request.form.get("emergency_number"),
            "ADDRESS": request.form.get("address"),
            "ALTERNATIVE EMAIL": request.form.get("personal_email"),
            "E-MAIL": request.form.get("zahoree_email"),
            "BIRTHDAY": request.form.get("birthday"),
            "GENDER": request.form.get("gender"),
            
            "STATUS": "Active"
        }

        supabase.table("Infolink_Staff").insert(new_data).execute()
        return redirect(url_for("index"))
    except Exception as e:
        return f"<h1>Error al Crear Registro</h1><p>Detalle: {e}</p>", 500

# Update
@app.route("/edit/<string:ID>", methods=["GET"])
def show_edit_form(ID):
    try:
        response = supabase.table("Infolink_Staff").select("*").eq("ID", ID).execute()
        record = response.data[0] if response.data else None
        if not record:
            abort(404)
        return render_template("edit.html", record=record)
    except Exception as e:
        return f"<h1>Error al Cargar Registro</h1><p>Detalle: {e}</p>", 500

#Enviar datos
@app.route("/edit/<string:ID>", methods=["POST"])
def update_record(ID):
    try:
        updated_data = {
            "nombre_columna_1": request.form.get("campo_1"),
            "nombre_columna_2": request.form.get("campo_2") 
        }

        supabase.table("Infolink_Staff").update(updated_data).eq("ID", ID).execute()
        return redirect(url_for("index"))
    except Exception as e:
        return f"<h1>Error al Actualizar Registro</h1><p>Detalle: {e}</p>", 500

@app.route("/employees")
def list_employees():
    try:
        # Parámetros de paginacion
        page = request.args.get("page", 1, type=int)
        if page < 1:
            page = 1
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page - 1

        # Filtros
        status = request.args.get("status", "Active")
        account = request.args.get("account", "")  # empty = no filter
        q = request.args.get("q", "").strip()

        # Construir filtros
        count_query = supabase.table("Infolink_Staff").select("*", count="exact")
        data_query = supabase.table("Infolink_Staff").select("*")

        if status:
            count_query = count_query.eq("STATUS", status)
            data_query = data_query.eq("STATUS", status)

        if account:
            count_query = count_query.eq("ACCOUNT", account)
            data_query = data_query.eq("ACCOUNT", account)

        if q:
            # ilike para buscar
            count_query = count_query.filter("FULL NAME", "ilike", f"%{q}%")
            data_query = data_query.filter("FULL NAME", "ilike", f"%{q}%")

        # Obtener total
        count_resp = count_query.execute()
        total = getattr(count_resp, "count", None)
        if total is None:
            # contar filas recibidas
            total = len(count_resp.data) if count_resp.data is not None else 0

        # Obtener pagina actual
        resp = data_query.range(start, end).execute()
        data = resp.data or []

        total_pages = (total + per_page - 1) // per_page if total else 1

        # Cuentas para llenar el select
        acc_resp = supabase.table("Infolink_Staff").select("ACCOUNT").execute()
        accounts = sorted({r.get("ACCOUNT") for r in (acc_resp.data or []) if r.get("ACCOUNT")})

        pagination = {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        }

        return render_template(
            "employees.html",
            employees=data,
            accounts=accounts,
            current_status=status,
            current_account=account,
            current_query=q,
            current_page=page,
            total_pages=total_pages,
            total_records=total
        )

    except Exception as e:
        return f"<h1>Error de Conexión o Base de Datos</h1><p>Detalle: {e}</p>", 500

# Autocompletado de nombres en el buscador
@app.route("/employees/suggest")
def employees_suggest():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    try:
        resp = supabase.table("Infolink_Staff")\
            .select("FULL NAME")\
            .filter("FULL NAME", "ilike", f"%{q}%")\
            .limit(10)\
            .execute()

        names = []
        for r in (resp.data or []):
            name = r.get("FULL NAME")
            if name and name not in names:
                names.append(name)
        return jsonify(names)
    except Exception:
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)