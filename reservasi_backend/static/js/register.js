document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('typed-text')) {
        var typed = new Typed('#typed-text', {
            strings: [
                "Akses Fitur Eksklusif",
                "Dapatkan Pembaruan Terbaru",
                "Temukan Koneksi Baru",
                "Mulai Petualangan Anda",
                "Dan Banyak Lagi!"
            ],
            typeSpeed: 50,
            backSpeed: 25,
            loop: true,
            cursorChar: '|',
            smartBackspace: true,
        });
    }
});