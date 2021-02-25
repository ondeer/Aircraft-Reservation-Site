from flask import Flask,render_template,request,render_template_string,session,redirect,url_for,flash,g
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, UserManager, UserMixin
from sqlalchemy.sql import select
from sqlalchemy import create_engine,MetaData, Table, Column,Integer,String,ForeignKey,and_,desc
from datetime import datetime
from functools import wraps
from passlib.hash import sha256_crypt

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mssql://@ONDER/ucakRezervasyon?driver=SQL Server Native Client 11.0'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
app.secret_key="Önder Açıkgöz"

db=SQLAlchemy(app)

class tbl_musteri(db.Model,UserMixin):
    __tablename__="tbl_musteri"
    musteriId=db.Column(db.Integer(),primary_key=True)
    musteriAd=db.Column(db.String(25),nullable=False)
    musteriSoyad=db.Column(db.String(25),nullable=False)
    kullaniciAdi=db.Column(db.String(25),nullable=False)
    sifre=db.Column(db.String(125),nullable=False)
    bonus=db.Column(db.Integer(),nullable=True)
    #roles = db.relationship('tbl_role', secondary='tbl_MusteriRol')

class tbl_rol(db.Model,UserMixin):
    __tablename__="tbl_rol"
    rolId=db.Column(db.Integer(),primary_key=True)
    rol=db.Column(db.String())

class tbl_MusteriRol(db.Model,UserMixin):
    __tablename__="tbl_MusteriRol"
    MusteriRolId=db.Column(db.Integer(),primary_key=True)
    musteriId=db.Column(db.Integer(),db.ForeignKey("tbl_musteri.musteriId",ondelete="CASCADE"))
    rolId=db.Column(db.Integer(),db.ForeignKey("tbl_rol.rolId",ondelete="CASCADE"))

class tbl_fiyat(db.Model,UserMixin):
    __tablename__="tbl_fiyat"
    fiyatId=db.Column(db.Integer(),primary_key=True)
    rotaId=db.Column(db.Integer(),db.ForeignKey("tbl_rota.rotaId",ondelete="CASCADE"))
    sirketUcakId=db.Column(db.Integer(),db.ForeignKey("tbl_sirketUcak.sirketUcakId",ondelete="CASCADE"))
    fiyat=db.Column(db.Integer())
    
class tbl_rezervasyon(db.Model,UserMixin):
    __tablename__="tbl_rezervasyon"
    rezervasyonId=db.Column(db.Integer(),primary_key=True)
    ucusId=db.Column(db.Integer(),db.ForeignKey("tbl_ucus.ucusId",ondelete="CASCADE"))
    musteriId=db.Column(db.Integer(),db.ForeignKey("tbl_musteri.musteriId",ondelete="CASCADE"))
    rezervasyonTarih=db.Column(db.DateTime())
    odemeYapildiMi=db.Column(db.Boolean())
    rBiletSahibiAd=db.Column(db.String(25))
    rBiletSahibiSoyad=db.Column(db.String(25))
    rBiletSahibiTC=db.Column(db.String(11))
    
class tbl_rota(db.Model,UserMixin):
    __tablename__="tbl_rota"
    rotaId=db.Column(db.Integer(),primary_key=True)
    kalkisSehirId=db.Column(db.Integer(),db.ForeignKey("tbl_sehir.sehirId",ondelete="CASCADE"))
    varisSehirId=db.Column(db.Integer(),db.ForeignKey("tbl_sehir.sehirId",ondelete="CASCADE"))
    
class tbl_sehir(db.Model,UserMixin):
    __tablename__="tbl_sehir"
    sehirId=db.Column(db.Integer(),primary_key=True)
    sehirAd=db.Column(db.String(25))
    ulkeId=db.Column(db.Integer(),db.ForeignKey("tbl_ulke.ulkeId",ondelete="CASCADE"))

class tbl_sirket(db.Model,UserMixin):
    __tablename__="tbl_sirket"
    sirketId=db.Column(db.Integer(),primary_key=True)
    sirketAd=db.Column(db.String(50))
    
class tbl_sirketUcak(db.Model,UserMixin):
    __tablename__="tbl_sirketUcak"
    sirketUcakId=db.Column(db.Integer(),primary_key=True)
    sirketId=db.Column(db.Integer(),ForeignKey("tbl_sirket.sirketId",ondelete="CASCADE"))
    ucakId=db.Column(db.Integer(),ForeignKey("tbl_ucak.ucakId",ondelete="CASCADE"))
    
class tbl_ucak(db.Model,UserMixin):
    __tablename__="tbl_ucak"
    ucakId=db.Column(db.Integer(),primary_key=True)
    ucakModel=db.Column(db.String())
    ucakKoltukSayisi=db.Column(db.Integer())
    
class tbl_ucus(db.Model,UserMixin):
    __tablename__="tbl_ucus"
    ucusId=db.Column(db.Integer(),primary_key=True)
    fiyatId=db.Column(db.Integer(),ForeignKey("tbl_fiyat.fiyatId",ondelete="CASCADE"))
    ucusTarih=db.Column(db.DateTime())
    ucusSaat=db.Column(db.String(10))
    ucusSilindiMi=db.Column(db.Boolean())
    ucusKontenjan=db.Column(db.Integer())
    kalanKontenjan=db.Column(db.Integer())
    yogunluk=db.Column(db.Numeric(precision=18, scale=2))

class tbl_ulke(db.Model,UserMixin):
    __tablename__="tbl_ulke"
    ulkeId=db.Column(db.Integer(),primary_key=True)
    ulkeAd=db.Column(db.String(25))

db.metadata.clear()
db.create_all()

class Sepet:
    i=0
    urunler={}

#Giriş yapılmış mı? bunu kontrol eder.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "girisYapildiMi" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız...","danger")
            return redirect(url_for("uye_giris"))
    return decorated_function

def roles_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "girisYapildiMi" in session:
            if tbl_MusteriRol.query.filter(tbl_MusteriRol.musteriId==session["kullaniciId"]).first():
                gelenVeri=tbl_MusteriRol.query.filter(tbl_MusteriRol.musteriId==session["kullaniciId"]).first()
                gelenVeri2=tbl_rol.query.filter(tbl_rol.rol=="Admin").first()
                if gelenVeri.rolId==gelenVeri2.rolId:
                    return f(*args, **kwargs)
                else:
                    flash("Bu sayfayı görüntülemek için Admin yetkinizin olması gerek...","danger")
                    return redirect(url_for("anasayfa"))
            else:
                flash("Bu sayfayı görüntüleme yetkiniz yok...","danger")
                return redirect(url_for("anasayfa"))
        else:
            flash("Bu sayfayı görüntülemek için Admin yetkinizin olması gerekir...","danger")
            return redirect(url_for("uye_giris"))
    return decorated_function

@app.route("/",methods=["GET","POST"])
def anasayfa():
    if request.method=="GET":
        sehirler = db.session.query(tbl_sehir).order_by(tbl_sehir.sehirAd).all()
        return render_template("Anasayfaa.html",sehirler=sehirler)
    
    else:
        secilenTarih = request.form["secilenTarih"]
        secilenKalkisSehir = request.form["secilenKalkisSehir"]
        secilenVarisSehir=request.form["secilenVarisSehir"]

        secilenKalkisSehirId=db.session.query(tbl_sehir.sehirId).filter_by(sehirAd=secilenKalkisSehir).first()
        secilenKalkisSehirId=str(secilenKalkisSehirId)[1:-2]
        

        secilenVarisSehirId=db.session.query(tbl_sehir.sehirId).filter_by(sehirAd=secilenVarisSehir).first()
        secilenVarisSehirId=str(secilenVarisSehirId)[1:-2]
        

        ucuslar = db.session.query(tbl_ucus,tbl_fiyat,tbl_sirket,tbl_ucak).filter(tbl_ucus.fiyatId==tbl_fiyat.fiyatId).filter(tbl_fiyat.rotaId==tbl_rota.rotaId).filter(tbl_rota.kalkisSehirId==secilenKalkisSehirId).filter(tbl_rota.varisSehirId==secilenVarisSehirId).filter(tbl_fiyat.sirketUcakId==tbl_sirketUcak.sirketUcakId).filter(tbl_sirketUcak.sirketId==tbl_sirket.sirketId).filter(tbl_sirketUcak.ucakId==tbl_ucak.ucakId).filter(tbl_ucus.ucusSilindiMi==False).filter(tbl_ucus.ucusTarih==secilenTarih).all()
        
        sehirler=db.session.query(tbl_sehir).all()

        if ucuslar:
            return render_template("anasayfa.html",kalkisSehir=secilenKalkisSehir,varisSehir=secilenVarisSehir,ucuslar=ucuslar,sehirler=sehirler)
        else:
            flash("Uçuş bulunamadı...","danger")
            return render_template("Anasayfaa.html",sehirler=sehirler)
        # flash(str(secilenKalkisSehir)+ " "+str(secilenVarisSehir)+ " "+ str(secilenTarih),"success")
        # return render_template("anasayfa.html")
    
@app.route("/uye_ol",methods=["GET","POST"])
def uye_ol():
    if request.method=="POST":
        try:
            isim=request.form["musteriAd"]
            soyisim=request.form["musteriSoyad"]
            kullaniciAdi=request.form["kullaniciAdi"]
            sifre=request.form["sifre"]
            musteri=tbl_musteri(
                musteriAd=isim,
                musteriSoyad=soyisim,
                kullaniciAdi=kullaniciAdi,
                sifre=sha256_crypt.hash(sifre),
                bonus=0
            )
            
            db.session.add(musteri)
            db.session.commit()
            
            flash("Kayıt İşleminiz Gerçekleştirildi...","success")
            
            return redirect(url_for("uye_giris"))

        except:
            flash("Kayıt İşleminiz Gerçekleştirilemedi...","danger")
            return render_template("uye_ol.html")
    else:
        return render_template("uye_ol.html")

@app.route("/uye_giris",methods=["GET","POST"])
def uye_giris():
    if request.method == "POST":
        girilenKullaniciAdi=request.form["kullaniciAdi"]
        girilenSifre=request.form["sifre"]
        
        if tbl_musteri.query.filter(tbl_musteri.kullaniciAdi==girilenKullaniciAdi).first():
            gelenVeri = tbl_musteri.query.filter(tbl_musteri.kullaniciAdi==girilenKullaniciAdi).first()
            if sha256_crypt.verify(girilenSifre,gelenVeri.sifre):
                flash("Giriş işlemi başarılı...","success")
                session["girisYapildiMi"]=True
                session["kullaniciAdi"]=gelenVeri.kullaniciAdi
                session["kullaniciId"]=gelenVeri.musteriId
                global sepet
                sepet=Sepet()
                return redirect(url_for("anasayfa"))
            else:
                flash("Girdiğiniz şifre yanlış","danger")
                return render_template("uye_giris.html")
        
        else:
            flash("Böyle bir kullanıcı yok","danger")
            return redirect(url_for("uye_giris"))
    
    else:
        return render_template("uye_giris.html")

@app.route("/uye_cikis")
def cikisYap():
    session.clear()
    global sepet
    sepet.urunler.clear()
    return redirect(url_for("anasayfa"))

@app.route("/admin")
@roles_required
def admin():
    return render_template("admin.html")

@app.route("/sirket_ekle",methods=["GET","POST"])
@roles_required
def sirket_ekle():
    if request.method=="POST":
        try:
            girilenSirketAdi=request.form["sirketAdi"]
            varMi=tbl_sirket.query.filter_by(sirketAd=girilenSirketAdi).first()
            if varMi:
                flash("Böyle bir şirket zaten var...","danger")
                return redirect(url_for("sirket_ekle"))
            else:
                sirket = tbl_sirket(
                    sirketAd=girilenSirketAdi,
                )

                db.session.add(sirket)
                db.session.commit()

                flash("Şirket ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except Exception as hata:
            flash("Ekleme sırasında hata oluştu..."+"Hata: " +str(hata),"danger")
            return redirect(url_for("sirket_ekle"))
    else:
        return render_template("sirket_ekle.html")


@app.route("/ucak_ekle",methods=["GET","POST"])
@roles_required
def ucak_ekle():
    if request.method=="POST":
        try:
            girilenUcakModeli=request.form["ucakModeli"]
            girilenKoltukSayisi=request.form["ucakKoltukSayisi"]
            secilenSirket=int(request.form["sirket"])
            
            ucakVarMi = tbl_ucak.query.filter_by(ucakModel=girilenUcakModeli).first()
            
            if ucakVarMi:
                flash("Böyle bir uçak zaten var...","success")
                return redirect(url_for("admin"))
                    
            else:
                ucak = tbl_ucak(
                ucakModel=girilenUcakModeli,
                ucakKoltukSayisi=girilenKoltukSayisi
                )

                db.session.add(ucak)
                db.session.commit()

                sorgu=tbl_ucak.query.filter(tbl_ucak.ucakModel==girilenUcakModeli).first()
                eklenenUcakId=sorgu.ucakId

                sirketUcak = tbl_sirketUcak(
                sirketId=secilenSirket,
                ucakId=eklenenUcakId
                )

                db.session.add(sirketUcak)
                db.session.commit()

                flash("Uçak ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except Exception as hata:
            flash("Ekleme sırasında hata oluştu..." + " Hata: "+str(hata),"danger")
            return redirect(url_for("ucak_ekle"))
    else:
        sirketler=db.session.query(tbl_sirket).order_by(tbl_sirket.sirketAd).all()
        return render_template("ucak_ekle.html",sirketler=sirketler)

@app.route("/ulke_ekle",methods=["GET","POST"])
@roles_required
def ulke_ekle():
    if request.method=="POST":
        try:
            girilenUlkeAdi=request.form["ulkeAd"]
            
            ulkeVarMi=db.session.query(tbl_ulke).filter_by(ulkeAd=girilenUlkeAdi).first()
            if ulkeVarMi:
                flash("Bu ülke zaten var...","danger")
                return redirect(url_for("ulke_ekle"))
            else:
                ulke = tbl_ulke(
                    ulkeAd=girilenUlkeAdi
                )

                db.session.add(ulke)
                db.session.commit()

                flash("Ülke ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except Exception as hata:
            flash("Ekleme sırasında hata oluştu...: " +str(hata),"danger")
            return redirect(url_for("ulke_ekle"))
    else:
        return render_template("ulke_ekle.html")

@app.route("/sehir_ekle",methods=["GET","POST"])
@roles_required
def sehir_ekle():
    if request.method=="POST":
        try:
            girilenSehir=request.form["sehir"]

            sehirVarMi=db.session.query(tbl_sehir).filter_by(sehirAd=girilenSehir).first()
            
            if sehirVarMi:
                flash("Bu şehir zaten var...","danger")
                return redirect(url_for("sehir_ekle"))
            else:
                secilenUlke=int(request.form["ulke"])
                sehir = tbl_sehir(
                    sehirAd=girilenSehir,
                    ulkeId=secilenUlke
                )

                db.session.add(sehir)
                db.session.commit()

            

                flash("Şehir ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("sehir_ekle"))
    else:
        ulkeler=db.session.query(tbl_ulke).order_by(tbl_ulke.ulkeAd).all()
        return render_template("sehir_ekle.html",ulkeler=ulkeler)

@app.route("/rota_ekle",methods=["GET","POST"])
@roles_required
def rota_ekle():
    if request.method=="POST":
        try:
            secilenKalkisSehri=int(request.form["kalkisSehri"])
            secilenVarisSehri=int(request.form["varisSehri"])

            rotaVarMi=db.session.query(tbl_rota).filter(tbl_rota.kalkisSehirId==secilenKalkisSehri).filter(tbl_rota.varisSehirId==secilenVarisSehri).first()
            
            if rotaVarMi:
                flash("Bu rota zaten var...","danger")
                return redirect(url_for("rota_ekle"))
            else:
                rota = tbl_rota(
                    kalkisSehirId=secilenKalkisSehri,
                    varisSehirId=secilenVarisSehri
                )

                db.session.add(rota)
                db.session.commit()

                flash("Rota ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("rota_ekle"))
    else:
        sehirler=db.session.query(tbl_sehir).all()
        return render_template("rota_ekle.html",sehirler=sehirler)

@app.route("/fiyat_ekle",methods=["GET","POST"])
@roles_required
def fiyat_ekle():
    if request.method=="POST":
        try:
            secilenRota = request.form["rota"]
            secilenSirketUcak=request.form["sirketUcak"]
            girilenFiyat=request.form["fiyat"]
            
            fiyat=tbl_fiyat(
                rotaId=secilenRota,
                sirketUcakId=secilenSirketUcak,
                fiyat=girilenFiyat
            )

            db.session.add(fiyat)
            db.session.commit()

            

            flash("Fiyat ekleme başarılı...","success")
            return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("fiyat_ekle"))
    else:
        diziRotalar=dict()
        rotalar=db.session.query(tbl_rota).all()
        for rota in rotalar:
            s = select([tbl_sehir.sehirAd]).where(tbl_sehir.sehirId == rota.kalkisSehirId)
            for row in db.session.execute(s):
                kalkisSehri=str(row)[2:-3]
    
            s=select([tbl_sehir.sehirAd]).where(tbl_sehir.sehirId == rota.varisSehirId)
            for row in db.session.execute(s):
                varisSehri=str(row)[2:-3]
            
            diziRotalar[rota.rotaId]={"kalkisSehri":kalkisSehri,"varisSehri":varisSehri}

        dictSirketUcak=dict()
        sirketUcak=db.session.query(tbl_sirketUcak).all()

        for sU in sirketUcak:
            s=select([tbl_sirket.sirketAd]).where(tbl_sirket.sirketId == sU.sirketId)
            for row in db.session.execute(s):
                sirketAd=str(row)[2:-3]

            s=select([tbl_ucak.ucakModel]).where(tbl_sirketUcak.ucakId==sU.ucakId)
            for row in db.session.execute(s):
                ucakModel=str(row)[2:-3]
            
            dictSirketUcak[sU.sirketUcakId]={"sirket":sirketAd,"ucakModel":ucakModel}
        
        return render_template("fiyat_ekle.html",rotalar=diziRotalar,sirketUcak=dictSirketUcak)

@app.route("/ucus_ekle",methods=["GET","POST"])
@roles_required
def ucus_ekle():
    if request.method=="POST":
        try:
            secilenUcus=request.form["ucus"]
            ucusTarihi=request.form["ucusTarihi"]
            ucusSaati=request.form["ucusSaati"]

            sorgu = db.session.query(tbl_ucus).filter(tbl_ucus.fiyatId==secilenUcus).filter(tbl_ucus.ucusTarih==ucusTarihi).filter(tbl_ucus.ucusSaat==ucusSaati).first()
            if sorgu:
                if sorgu.ucusSilindiMi==True:
                    sorgu.ucusSilindiMi=False
                    db.session.commit()
                else:
                    flash("Bu uçuş zaten ekli...","danger")
                    return redirect(url_for("admin"))
            else:
                ucusKontenjan = db.session.query(tbl_ucak.ucakKoltukSayisi).filter(tbl_fiyat.fiyatId==secilenUcus).filter(tbl_sirketUcak.sirketUcakId==tbl_fiyat.sirketUcakId).filter(tbl_ucak.ucakId==tbl_sirketUcak.ucakId).first()
                ucusKontenjan = str(ucusKontenjan)[1:-2]
                ucus=tbl_ucus(
                    fiyatId=secilenUcus,
                    ucusTarih=ucusTarihi,
                    ucusSaat=ucusSaati,
                    ucusKontenjan=ucusKontenjan,
                    kalanKontenjan=ucusKontenjan,
                    ucusSilindiMi=False,
                    yogunluk=0
                 )

                db.session.add(ucus)
                db.session.commit()

                flash("Uçuş ekleme başarılı..."+str(ucusKontenjan),"success")
                return redirect(url_for("admin"))
        
        except Exception as hata:
            flash("Ekleme sırasında hata oluştu..."+str(hata),"danger")
            return redirect(url_for("ucus_ekle"))
    else:
        dictUcus=dict()
        fiyatlar = db.session.query(tbl_fiyat).all()
        
        for fiyat in fiyatlar:
            s=db.session.query(tbl_sehir.sehirAd).filter(tbl_rota.kalkisSehirId==tbl_sehir.sehirId).filter(tbl_rota.rotaId==tbl_fiyat.rotaId).filter(tbl_fiyat.fiyatId==fiyat.fiyatId)
            for row in s:
                kalkisSehri=str(row)[2:-3]
            
            s=db.session.query(tbl_sehir.sehirAd).filter(tbl_rota.varisSehirId==tbl_sehir.sehirId).filter(tbl_rota.rotaId==tbl_fiyat.rotaId).filter(tbl_fiyat.fiyatId==fiyat.fiyatId)
            for row in s:
                varisSehri=str(row)[2:-3]
            
            s=db.session.query(tbl_sirket.sirketAd).filter(tbl_sirket.sirketId==tbl_sirketUcak.sirketId).filter(tbl_sirketUcak.sirketUcakId==fiyat.sirketUcakId)
            for row in s:
                ucusSirketi=str(row)[2:-3]

            # s=db.session.query(tbl_ucak.ucakModel).filter(tbl_ucak.ucakId==tbl_sirketUcak.ucakId).filter(tbl_sirketUcak.sirketUcakId==fiyat.sirketUcakId)
            s=db.session.query(tbl_ucak).filter(tbl_ucak.ucakId==tbl_sirketUcak.ucakId).filter(tbl_sirketUcak.sirketUcakId==fiyat.sirketUcakId)
            for row in s:
                # ucusUcakModeli=str(row)[2:-3]
                ucusUcakModeli=row.ucakModel
                ucusUcakKoltukSayisi=row.ucakKoltukSayisi

            ucusFiyati=fiyat.fiyat

            # dictUcus[fiyat.fiyatId]={"kalkisSehri":kalkisSehri,"varisSehri":varisSehri,"ucusSirketi":ucusSirketi,"ucusUcakModeli":ucusUcakModeli,"ucusFiyati":ucusFiyati}
            dictUcus[fiyat.fiyatId]={"kalkisSehri":kalkisSehri,"varisSehri":varisSehri,"ucusSirketi":ucusSirketi,"ucusUcakModeli":ucusUcakModeli,"ucusUcakKoltukSayisi":ucusUcakKoltukSayisi,"ucusFiyati":ucusFiyati}


            
        
        return render_template("ucus_ekle.html",fiyatlar=dictUcus)        

@app.route("/ucus_duzenle",methods=["GET","POST"])
@roles_required
def ucus_duzenle():
    global secilenUcus
    if request.method=="GET":
        global secilenUcus
        secilenUcus = request.args.get("ucus_id")
        dictRotalar=dict()
        rotalar= db.session.query(tbl_rota).all()
        for rota in rotalar:
            kalkisSehir=db.session.query(tbl_sehir).filter_by(sehirId=rota.kalkisSehirId).first()
            varisSehir=db.session.query(tbl_sehir).filter_by(sehirId=rota.varisSehirId).first()
            dictRotalar[rota.rotaId]={"kalkisSehir":kalkisSehir.sehirAd,"kalkisSehirId":kalkisSehir.sehirId,"varisSehir":varisSehir.sehirAd,"varisSehirId":varisSehir.sehirId}

        sirketler=db.session.query(tbl_sirket).all()
        ucaklar=db.session.query(tbl_ucak).all()
        return render_template("ucus_duzenle.html",dictRotalar=dictRotalar,sirketler=sirketler,ucaklar=ucaklar)
    else:
        try:
            secilenRota=request.form["secilenRota"]
            girilenFiyat=request.form["girilenFiyat"]
            secilenSirket=request.form["secilenSirket"]
            secilenUcak=request.form["secilenUcak"]
            girilenUcusSaati=request.form["girilenSaat"]
            girilenUcusTarihi=request.form["secilenTarih"]

            ucusBilgileri=db.session.query(tbl_ucus,tbl_fiyat,tbl_rota,tbl_sirketUcak).filter(tbl_ucus.fiyatId==tbl_fiyat.fiyatId).filter(tbl_fiyat.rotaId==tbl_rota.rotaId).filter(tbl_fiyat.sirketUcakId==tbl_sirketUcak.sirketUcakId).filter(tbl_sirketUcak.ucakId==tbl_ucak.ucakId).filter(tbl_sirketUcak.sirketId==tbl_sirket.sirketId).filter(tbl_ucus.ucusId==secilenUcus).first()
            
            ucusBilgileri[0].ucusTarih=girilenUcusTarihi
            ucusBilgileri[0].ucusSaat=girilenUcusSaati
            ucusBilgileri[1].fiyat=girilenFiyat
            ucusBilgileri[1].rotaId=secilenRota
            ucusBilgileri[3].sirketId=secilenSirket
            ucusBilgileri[3].ucakId=secilenUcak

            db.session.commit()
            
            flash(str(ucusBilgileri)+"Güncelleme başarılı...","success")
            return redirect(url_for("admin"))
        except Exception as hata:
            flash("Güncelleme sırasında hata oluştu: " + str(hata),"danger")

@app.route("/ucus_sil",methods=["GET"])
@roles_required
def ucus_sil():
    try:
        secilenUcus = request.args.get("ucus_id")
        ucus=db.session.query(tbl_ucus).filter_by(ucusId=secilenUcus).first()
        ucus.ucusSilindiMi=True
        db.session.commit()

        flash("Uçuş silme işlemi başarılı...","success")
        return redirect(url_for("admin"))

    except Exception as hata:
        flash("Silme işlemi sırasında hata oluştu... " + str(hata),"danger")
        return redirect(url_for("ucuslar"))

        
@app.route("/ucuslar",methods=["GET","POST"])
@roles_required
def ucuslar():
    if request.method=="GET":
        dictUcuslar=dict()
        
        ucuslar=db.session.query(tbl_ucus,tbl_fiyat,tbl_rota,tbl_sirket,tbl_ucak).filter(tbl_ucus.fiyatId==tbl_fiyat.fiyatId).filter(tbl_fiyat.rotaId==tbl_rota.rotaId).filter(tbl_fiyat.sirketUcakId==tbl_sirketUcak.sirketUcakId).filter(tbl_sirketUcak.ucakId==tbl_ucak.ucakId).filter(tbl_sirketUcak.sirketId==tbl_sirket.sirketId).all()
        
        for ucus in ucuslar:
            kalkisSehir=db.session.query(tbl_sehir.sehirAd).filter(tbl_sehir.sehirId==ucus[2].kalkisSehirId).first()
            kalkisSehir=str(kalkisSehir)[2:-3]

            varisSehir=db.session.query(tbl_sehir.sehirAd).filter(tbl_sehir.sehirId==ucus[2].varisSehirId).first()
            varisSehir=str(varisSehir)[2:-3]

            fiyat=db.session.query(tbl_fiyat.fiyat).filter_by(fiyatId=ucus[1].fiyatId).first()
            fiyat=str(fiyat)[10:-4]

            sirket=db.session.query(tbl_sirket.sirketAd).filter_by(sirketId=ucus[3].sirketId).first()
            sirket=str(sirket)[2:-3]

            ucak=db.session.query(tbl_ucak.ucakModel).filter_by(ucakId=ucus[4].ucakId).first()
            ucak=str(ucak)[2:-3]


            dictUcuslar[ucus[0].ucusId]={"kalkisSehir":kalkisSehir,"varisSehir":varisSehir,"fiyat":fiyat,"sirket":sirket,"ucak":ucak,"ucusTarih":ucus[0].ucusTarih,"ucusSaat":ucus[0].ucusSaat}
            
        return render_template("ucuslar.html",ucuslar=dictUcuslar)
 

@app.route("/rezervasyon_yap",methods=["GET","POST"])
@login_required
def rezervasyon_yap():
    
    if request.method == "GET":
        global secilenUcusId
        secilenUcusId=request.args.get('ucus_id')
        flash(str(secilenUcusId),"success")
        return render_template("rezervasyon_yap.html",ucusId=secilenUcusId)
    else:
        global ucusId
        ucusId=secilenUcusId
        ucus=db.session.query(tbl_rota).filter(tbl_ucus.ucusId==ucusId).filter(tbl_fiyat.fiyatId==tbl_ucus.fiyatId).filter(tbl_fiyat.rotaId==tbl_rota.rotaId).first()
        kalkisSehir=db.session.query(tbl_sehir.sehirAd).filter_by(sehirId=ucus.kalkisSehirId).first()
        kalkisSehir=str(kalkisSehir)[2:-3]
        varisSehir=db.session.query(tbl_sehir.sehirAd).filter_by(sehirId=ucus.varisSehirId).first()
        varisSehir=str(varisSehir)[2:-3]

        global sepet
        biletSahibiAdi=request.form["biletSahibiAd"]
        biletSahibiSoyadi=request.form["biletSahibiSoyad"]
        biletSahiciTC=request.form["biletSahibiTC"]
        simdi=datetime.now()    
        sepet.urunler[sepet.i]={"ucusId":ucusId,"rezervasyonSaati":simdi,"biletSahibiAd":biletSahibiAdi,"biletSahibiSoyad":biletSahibiSoyadi,"biletSahibiTC":biletSahiciTC,"kalkisSehir":kalkisSehir,"varisSehir":varisSehir}
        sepet.i=sepet.i+1
        flash("ürünler sepete eklendi...","success")
        return redirect(url_for("anasayfa"))
        

        # rezervasyon=tbl_rezervasyon(
        #     ucusId=secilenUcusId,
        #     musteriId=session["kullaniciId"],
        #     rezervasyonTarih=datetime.now,
        #     odemeYapildiMi=False,
        #     rBiletSahibiAd=biletSahibiAdi,
        #     rBiletSahibiSoyad=biletSahibiSoyadi,
        #     rBiletSahibiTC=biletSahiciTC
        # )

        # db.session.add(rezervasyon)
        # db.session.commit()

@app.route("/rezervasyon_guncelle",methods=["GET","POST"])
@login_required
def rezervasyon_guncelle():
    global secilenRezervasyon
    if request.method=="GET":
        global secilenRezervasyon
        secilenRezervasyon=request.args.get('sepetKey')
        secilenRezervasyon=int(secilenRezervasyon)
        return render_template("rezervasyon_guncelle.html")
    else:
        global sepet
        
        biletSahibiAdi=request.form["biletSahibiAd"]
        biletSahibiSoyadi=request.form["biletSahibiSoyad"]
        biletSahiciTC=request.form["biletSahibiTC"]
        
        sepet.urunler[secilenRezervasyon]["biletSahibiTC"]=biletSahiciTC
        sepet.urunler[secilenRezervasyon]["biletSahibiSoyad"]=biletSahibiSoyadi
        sepet.urunler[secilenRezervasyon]["biletSahibiAd"]=biletSahibiAdi

        flash("Güncelleme başarılı...","success")
        return redirect(url_for("sepet"))
        
@app.route("/sepet",methods=["GET","POST"])
@login_required
def sepet():
    if request.method=="GET":
        global sepet
        simdi=datetime.now()
        for urun in list(sepet.urunler.keys()):
            rezervasyonSaati=sepet.urunler[urun]["rezervasyonSaati"]
            sonuc=simdi-rezervasyonSaati
            if (sonuc.seconds)/60 >1:  
                del sepet.urunler[urun] 
        return render_template("sepet.html",spt=sepet.urunler)

@app.route("/odeme_yap",methods=["POST","GET"])
@login_required
def odeme_yap():
    global secilenRezervasyon
    if request.method=="GET":
        global sepet

        global secilenRezervasyon
        secilenRezervasyon=request.args.get('sepetKey')
        secilenRezervasyon=int(secilenRezervasyon)

        
        s = db.session.query(tbl_fiyat.fiyat).filter(tbl_fiyat.fiyatId==tbl_ucus.fiyatId).filter(tbl_ucus.ucusId==sepet.urunler[secilenRezervasyon]["ucusId"])
        for row in s:
            tutar=str(row)[10:-4]
        
        s=db.session.query(tbl_musteri.bonus).filter(tbl_musteri.musteriId==session["kullaniciId"])
        for row in s:
            bonus=str(row)[1:-2]
        
        return render_template("odeme_yap.html",tutar=tutar,bonus=bonus,spt=sepet.urunler[secilenRezervasyon])

    else:
        bonus=request.form["kullanilanBonus"]
        tutar=request.form["tutar"]
        sonuc=float(tutar)-float(bonus)
        kazanılanBonus = (float(sonuc)*3)/100

        # simdi=time.strftime(r"%d.%m.%Y %H:%M:%S", time.localtime())
        simdi=datetime.now()

        rezervasyon = tbl_rezervasyon(
            ucusId=sepet.urunler[secilenRezervasyon]["ucusId"],
            musteriId=session["kullaniciId"],
            rezervasyonTarih=sepet.urunler[secilenRezervasyon]["rezervasyonSaati"],
            odemeYapildiMi=True,
            rBiletSahibiAd=sepet.urunler[secilenRezervasyon]["biletSahibiAd"],
            rBiletSahibiSoyad=sepet.urunler[secilenRezervasyon]["biletSahibiSoyad"],
            rBiletSahibiTC=sepet.urunler[secilenRezervasyon]["biletSahibiTC"]
            )
        db.session.add(rezervasyon)
        db.session.commit()

        sorgu=tbl_ucus.query.filter_by(ucusId=sepet.urunler[secilenRezervasyon]["ucusId"]).first()
        sorgu.kalanKontenjan=sorgu.kalanKontenjan-1

        yogunluk=((sorgu.ucusKontenjan-sorgu.kalanKontenjan)/sorgu.ucusKontenjan)*100

        sorgu.yogunluk=yogunluk

        db.session.commit()

        musteri = tbl_musteri.query.filter_by(musteriId=session["kullaniciId"]).first()
        musteri.bonus=float(musteri.bonus)+float(kazanılanBonus)-float(bonus)
        db.session.commit()

        del sepet.urunler[secilenRezervasyon]

        flash(str(sorgu)+" Rezervasyonunuz gerçekleştirildi. Ödediğiniz tutar: " + str(sonuc) + "Türk Lirası","success")
        return redirect(url_for("anasayfa"))

    
@app.route("/rezervasyonlarım",methods=["GET"])
@login_required
def rezervasyonlarım():
    dictRezervasyonlar=dict()
    rezervasyonlar = db.session.query(tbl_rezervasyon).filter(tbl_rezervasyon.musteriId==session["kullaniciId"])
    
    
        
    
    for rezervasyon in rezervasyonlar:
        ucus=db.session.query(tbl_rota).filter(tbl_ucus.ucusId==rezervasyon.ucusId).filter(tbl_fiyat.fiyatId==tbl_ucus.fiyatId).filter(tbl_fiyat.rotaId==tbl_rota.rotaId).first()
        kalkisSehir=db.session.query(tbl_sehir.sehirAd).filter_by(sehirId=ucus.kalkisSehirId).first()
        kalkisSehir=str(kalkisSehir)[2:-3]
        varisSehir=db.session.query(tbl_sehir.sehirAd).filter_by(sehirId=ucus.varisSehirId).first()
        varisSehir=str(varisSehir)[2:-3]
        

        dictRezervasyonlar[rezervasyon.rezervasyonId]={"kalkisSehir":kalkisSehir,"varisSehir":varisSehir,"rezervasyonTarih":rezervasyon.rezervasyonTarih,"rBiletSahibiAd":rezervasyon.rBiletSahibiAd,"rBiletSahibiSoyad":rezervasyon.rBiletSahibiSoyad,"rBiletSahibiTC":rezervasyon.rBiletSahibiTC}
    return render_template("rezervasyonlarım.html",rezervasyonlarım=dictRezervasyonlar) 

@app.route("/rezervasyon_sil",methods=["GET"])
@login_required
def rezervasyon_sil():
    global secilenRezervasyon
    secilenRezervasyon=request.args.get("sepetKey")
    secilenRezervasyon=int(secilenRezervasyon)
    global sepet
    del sepet.urunler[secilenRezervasyon]

    flash("Silme işlemi başarılı...","success")
    return redirect(url_for("sepet"))

@app.route("/yogunluk",methods=["POST","GET"])
@roles_required
def yogunluk():
    if request.method=="GET":
        return render_template("yogunluk.html")
    else:
        ucakYogunluk=dict()
        aralik1=request.form["aralik1"]
        aralik2=request.form["aralik2"]

        
        
        ucuslar=db.session.query(tbl_ucus,tbl_ucak).filter(and_(tbl_ucus.ucusTarih >= aralik1, tbl_ucus.ucusTarih <= aralik2)).filter(tbl_ucus.fiyatId==tbl_fiyat.fiyatId).filter(tbl_fiyat.sirketUcakId==tbl_sirketUcak.sirketUcakId).filter(tbl_sirketUcak.ucakId==tbl_ucak.ucakId).order_by(tbl_ucus.yogunluk.desc()).all()
        for ucus in ucuslar:
            ucakYogunluk[ucus[0].ucusId]={"yogunluk":ucus[0].yogunluk,"ucak":ucus[1].ucakModel,"tarih":ucus[0].ucusTarih,"saat":ucus[0].ucusSaat}

        flash(str(ucuslar)+"Seçtiğiniz tarih aralıklarına göre hesaplana yoğunluk = %","success")
        return render_template("ucak_yogunluk.html",ucuslar=ucakYogunluk)

@app.route("/sepeti_temizle")
@login_required
def sepeti_temizle():
    global sepet
    sepet.urunler.clear()
    flash("Sepet temizleme işlemi başarılı...","success")
    return redirect(url_for("sepet"))

        
if __name__ == '__main__':
   app.run(debug = True)