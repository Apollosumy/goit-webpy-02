import pickle
from abc import ABC, abstractmethod
from collections import UserDict
from datetime import datetime, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not self.is_valid_phone(value):
            raise ValueError("Invalid phone number format. Phone should consist of 10 digits.")
        super().__init__(value)

    @staticmethod
    def is_valid_phone(phone):
        return phone.isdigit() and len(phone) == 10

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            self.value = value
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return self

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return self
        raise ValueError("Phone number not found")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def get_days_to_birthday(self):
        if self.birthday:
            today = datetime.today()
            birthday_date = datetime.strptime(self.birthday.value, "%d.%m.%Y")
            next_birthday = birthday_date.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            return (next_birthday - today).days
        return None

    def __str__(self):
        phones_str = ', '.join(str(phone) for phone in self.phones)
        birthday_str = self.birthday.value if self.birthday else "N/A"
        return f"Ім'я: {self.name.value}, Телефони: {phones_str}, День народження: {birthday_str}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def get_upcoming_birthdays(self, days=7):
        today = datetime.today()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                days_to_birthday = record.get_days_to_birthday()
                if days_to_birthday is not None and days_to_birthday <= days:
                    birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y")
                    next_birthday = birthday_date.replace(year=today.year)
                    if next_birthday < today:
                        next_birthday = next_birthday.replace(year=today.year + 1)
                    if next_birthday.weekday() == 5:
                        next_birthday += timedelta(days=2)
                    elif next_birthday.weekday() == 6:
                        next_birthday += timedelta(days=1)
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": next_birthday.strftime("%d.%m.%Y")
                    })
        return upcoming_birthdays


class UserInterface(ABC):
    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_help(self):
        pass

class ConsoleInterface(UserInterface):
    def show_message(self, message):
        print(message)

    def show_contacts(self, contacts):
        for contact in contacts:
            print(contact)

    def show_help(self):
        help_message = """
        Список доступних команд:
        - hello: Привітання
        - add <ім'я> <телефон>: Додати новий контакт
        - change <ім'я> <старий телефон> <новий телефон>: Змінити номер телефону контакту
        - phone <ім'я>: Показати номери телефону контакту
        - all: Показати всі контакти
        - add-birthday <ім'я> <дата>: Додати день народження контакту (формат дати: DD.MM.YYYY)
        - show-birthday <ім'я>: Показати день народження контакту
        - birthdays: Показати контакти з днями народження у найближчі 7 днів
        - close/exit: Вийти з програми
        """
        print(help_message)


def input_error(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (KeyError, ValueError, IndexError) as e:
            return str(e)
    return wrapper


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number updated for {name}."
    return "Contact not found."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return ', '.join(phone.value for phone in record.phones)
    return "Contact not found."

@input_error
def show_all(args, book: AddressBook):
    return str(book)

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday added for {name}."
    return "Contact not found."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return record.birthday.value
    return "Contact or birthday not found."

@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No birthdays in the next 7 days."
    return '\n'.join(f"{item['name']}: {item['birthday']}" for item in upcoming_birthdays)


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def process_command(command, args, book, interface):
    if command == "hello":
        interface.show_message("How can I help you?")
    elif command == "add":
        interface.show_message(add_contact(args.split(), book))
    elif command == "change":
        interface.show_message(change_contact(args.split(), book))
    elif command == "phone":
        interface.show_message(show_phone(args.split(), book))
    elif command == "all":
        interface.show_contacts(book.data.values())
    elif command == "add-birthday":
        interface.show_message(add_birthday(args.split(), book))
    elif command == "show-birthday":
        interface.show_message(show_birthday(args.split(), book))
    elif command == "birthdays":
        interface.show_message(birthdays(args.split(), book))
    elif command == "help":
        interface.show_help()
    elif command in ["close", "exit"]:
        interface.show_message("Good bye!")
        save_data(book)
        return False
    else:
        interface.show_message("Invalid command. Use 'help' to see available commands.")
    return True


def main():
    book = load_data()
    interface = ConsoleInterface()
    interface.show_message("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ").lower()
        command, args = user_input.split(maxsplit=1) if " " in user_input else (user_input, "")
        if not process_command(command, args, book, interface):
            break

if __name__ == "__main__":
    main()
