window.onload = function() {
    checkAuth();
};


function renderAuthPage(){
    const signOut = document.querySelector(".signout");
    const signinSignup = document.querySelector(".signin-signup");
    signinSignup.classList.add("hide");
    signOut.classList.remove("hide");
}


function renderUnauthPage(){
    const signOut = document.querySelector(".signout");
    const signinSignup = document.querySelector(".signin-signup");
    signOut.classList.add("hide");
    signinSignup.classList.remove("hide");
}


// 檢查 LocalStorage 中是否有 token
function checkAuth() {
    const token = localStorage.getItem("token");
    fetch("/api/user/auth",{
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`,
        }
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        user_info = data["data"]
        if (user_info === "null"){
            renderUnauthPage()
        }
        else{
            renderAuthPage()
        }
    })
}


document.addEventListener("DOMContentLoaded", () => {
    //回首頁
    const homebtn = document.querySelector(".left");
    homebtn.addEventListener("click", () => {
        window.location.href = "/";
    });
    //登入/註冊點擊
    const signinSignup = document.querySelector(".signin-signup");
    const signinDialog = document.getElementById("signinDialog");
    const signupDialog = document.getElementById("signupDialog");
    signinSignup.addEventListener("click", () => {
        signinDialog.showModal();
        signupDialog.close();
    });
    //處理尚未註冊點擊
    const goToSignup = document.getElementById("go-to-signup");
    goToSignup.addEventListener("click", () => {
        signinDialog.close();
        signupDialog.showModal();
    });
    //回到登入
    const backToSignin = document.getElementById("back-to-signin");
    backToSignin.addEventListener("click", () => {
        signinDialog.showModal();
        signupDialog.close();
    })
    //預定行程點擊
    const booking = document.querySelector(".booking");
    booking.addEventListener("click", () => {
        if (signinSignup.classList.contains("hide")) {
            window.location.href = "/booking";
        } else {
            signinDialog.showModal();
        }
    })
    //提交註冊表單
    signUp();
    //提交登入表單
    signIn();
    //點擊登出
    const signout = document.querySelector(".signout");
    signout.addEventListener("click", () => {
        localStorage.removeItem("token");
        window.location.reload()
    })
});


function signUp(){
    const signup = document.getElementById("signup");
    signup.addEventListener("submit",(e) => {
        e.preventDefault();
        const signupName = document.getElementById("signup-name").value;
        const signupEmail = document.getElementById("signup-email").value;
        const signupPassword =document.getElementById("signup-password").value;
        fetch("/api/user",{
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name: signupName, email: signupEmail, password: signupPassword })
        })
        .then(response => {return response.json()})
        .then(result => {
            if (result.ok) {
                const signupResponse = document.getElementById("signup-response");
                const signupFont = document.querySelector(".signup-font");
                signupResponse.textContent = "註冊成功，請登入系統";
                signupFont.style.color = "green";
                signupResponse.classList.remove("hide");
                setTimeout(() => {
                    signupResponse.classList.add("hide");
                }, 2000); // 2秒後隱藏
            } else {
                throw result;
            }
        })
        .catch(error => {
            console.error("Error", error);
            if (error.detail){
                const emailError = error.detail.find(e => e.loc.includes("email"));//遍歷detail列表，找到loc裡面有email的
                if (emailError) {
                    const signupResponse = document.getElementById("signup-response");
                    const signupFont = document.querySelector(".signup-font");
                    signupResponse.textContent = "電子郵件格式錯誤";
                    signupFont.style.color = "red";
                    signupResponse.classList.remove("hide");
                    setTimeout(() => {
                        signupResponse.classList.add("hide");
                    }, 2000); // 2秒後隱藏
                } 
            }
            if (error.message === "Email already registered") {
                const signupResponse = document.getElementById("signup-response");
                const signupFont = document.querySelector(".signup-font");
                signupResponse.textContent = "電子郵件已經註冊帳戶";
                signupFont.style.color = "red";
                signupResponse.classList.remove("hide");
                setTimeout(() => {
                    signupResponse.classList.add("hide");
                }, 2000); // 2秒後隱藏
            }
        });
    })
}


function signIn(){
    const signin = document.getElementById("signin");
    signin.addEventListener("submit",(e) => {
        e.preventDefault();
        const signinEmail = document.getElementById("signin-email").value;
        const signinPassword =document.getElementById("signin-password").value;
        fetch("/api/user/auth",{
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email: signinEmail, password: signinPassword })
        })
        .then(response => {return response.json()})
        .then(result => {
            token = result.token;
            if (token) {
                localStorage.setItem("token", token);
                //console.log(token)
                window.location.reload();
            } else {
                throw result;
            }
        })
        .catch(error => {
            console.error("Error", error);
            if (error.message === "Invalid email or password") {
                const signinResponse = document.getElementById("signin-response");
                const signinFont = document.querySelector(".signin-font");
                signinResponse.textContent = "電子郵件或密碼錯誤";
                signinFont.style.color = "red";
                signinResponse.classList.remove("hide");
                setTimeout(() => {
                    signinResponse.classList.add("hide");
                }, 2000); // 2秒後隱藏
            }
        });
    })
}


function closeDialog(dialogId) {
    document.getElementById(dialogId).close();
}
