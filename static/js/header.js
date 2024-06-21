document.addEventListener("DOMContentLoaded", () => {
    //回首頁
    const homebtn = document.querySelector(".left");
    homebtn.addEventListener("click", () => {
        window.location.href = "/";
    });
    //登入/註冊點擊
    const signinSignup = document.querySelector(".signin-signup");
    const signin = document.getElementById("signin");
    const signup = document.getElementById("signup");
    signinSignup.addEventListener("click", () => {
        signin.classList.remove("hide");
        signup.classList.add("hide");
    });
    //處理尚未註冊點擊
    const goToSignup = document.getElementById("go-to-signup");
    goToSignup.addEventListener("click", () => {
        signin.classList.add("hide");
        signup.classList.toggle("hide");
    });
    //回到註冊
    const backToSignin = document.getElementById("back-to-signin");
    backToSignin.addEventListener("click", () => {
        signup.classList.add("hide");
        signin.classList.toggle("hide");
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


function closeSignin(){
    const signin = document.getElementById("signin");
    signin.classList.add("hide");
}


function closeSignup(){
    const signup = document.getElementById("signup");
    signup.classList.add("hide");
}