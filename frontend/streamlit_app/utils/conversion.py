def fahrenheitToCelsius(originalTemp):
    return round((originalTemp - 32)/1.8, 2)

# small test suit, can write a more polished test suite in future 
if __name__ == "__main__":
    print("Inside of test suite, to be ran when file is not imported")
    fahrenheitList = [-40,-20,0,32,50,68]
    celsiusList = [-40.0,-28.9,-17.8,0.0,10.0,20.0]
    
    size = len(fahrenheitList)
    index = 0
    for oldTemp in fahrenheitList:
        convertedTemp = fahrenheitToCelsius(oldTemp)
        expectedTemp = celsiusList[index]
        assert(abs(convertedTemp - expectedTemp) < 0.1)
        index +=1

    print("Done testing unit conversion method")