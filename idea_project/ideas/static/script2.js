function saveProfile(event) {
    event.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const bio = document.getElementById('bio').value;

    console.log("Name:", name);
    console.log("Email:", email);
    console.log("Bio:", bio);

    // Your code to handle form submission, e.g., sending data to a server
}
