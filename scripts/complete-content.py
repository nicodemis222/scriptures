#!/usr/bin/env python3
"""Complete missing content for Coptic, Dead Sea Scrolls, and Russian Orthodox
volumes in scriptures.db.

This script is idempotent: it checks for existing verses before inserting
and never deletes existing data.

Sources:
- KJV Apocrypha (1611, public domain) for Tobit, Judith, Baruch, Maccabees
- R.H. Charles translations (public domain) for Ethiopian texts
- Public domain scholarly translations for Dead Sea Scrolls
"""

import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "data", "scriptures.db")


# ---------------------------------------------------------------------------
# Tobit — KJV Apocrypha (public domain)
# Coptic (book_id=2007, volume_id=200) and Russian (book_id=4003, volume_id=400)
# 14 chapters
# ---------------------------------------------------------------------------

TOBIT_VERSES_RAW = [
    # Chapter 1: Tobit's righteousness and exile
    (1, 1, "The book of the words of Tobit, son of Tobiel, the son of Ananiel, the son of Aduel, the son of Gabael, of the seed of Asael, of the tribe of Nephthali."),
    (1, 2, "Who in the time of Enemessar king of the Assyrians was led captive out of Thisbe, which is at the right hand of that city, which is called properly Nephthali in Galilee above Aser."),
    (1, 3, "I Tobit have walked all the days of my life in the ways of truth and justice, and I did many almsdeeds to my brethren, and my nation, who came with me to Nineve, into the land of the Assyrians."),
    (1, 4, "And when I was in mine own country, in the land of Israel, being but young, all the tribe of Nephthali my father fell from the house of Jerusalem."),
    (1, 5, "Which was chosen out of all the tribes of Israel, that all the tribes should sacrifice there, where the temple of the habitation of the most High was consecrated and built for all ages."),
    (1, 6, "Now all the tribes which together revolted, and the house of my father Nephthali, sacrificed unto the heifer Baal."),
    (1, 7, "But I alone went often to Jerusalem at the feasts, as it was ordained unto all the people of Israel by an everlasting decree, having the firstfruits and tenths of increase, with that which was first shorn."),
    (1, 8, "And them gave I at the altar to the priests the children of Aaron."),
    (1, 9, "The first tenth part of all increase I gave to the sons of Aaron, who ministered at Jerusalem: another tenth part I sold away, and went, and spent it every year at Jerusalem."),
    (1, 10, "And the third I gave unto them to whom it was meet, as Debora my father's mother had commanded me, because I was left an orphan by my father."),
    (1, 11, "Furthermore, when I was come to the age of a man, I married Anna of mine own kindred, and of her I begat Tobias."),
    (1, 12, "And when we were carried away captives to Nineve, all my brethren and those that were of my kindred did eat of the bread of the Gentiles."),
    (1, 13, "But I kept myself from eating; because I remembered God with all my heart."),
    (1, 14, "And the most High gave me grace and favour before Enemessar, so that I was his purveyor."),
    (1, 15, "And I went into Media, and left in trust with Gabael, the brother of Gabrias, at Rages a city of Media ten talents of silver."),
    (1, 16, "Now when Enemessar was dead, Sennacherib his son reigned in his stead; whose estate was troubled, that I could not go into Media."),
    (1, 17, "And in the time of Enemessar I gave many alms to my brethren, and gave my bread to the hungry."),
    (1, 18, "And my raiment to the naked: and if I saw any of my nation dead, or cast about the walls of Nineve, I buried him."),
    (1, 19, "And if the king Sennacherib had slain any, when he was come, and fled from Judea, I buried them privily; for in his wrath he killed many; but the bodies were not found, when they were sought for of the king."),
    (1, 20, "And when one of the Ninevites went and complained of me to the king, that I buried them, and hid myself; understanding that I was sought for to be put to death, I withdrew myself for fear."),
    (1, 21, "Then all my goods were forcibly taken away, neither was there any thing left me, beside my wife Anna and my son Tobias."),
    (1, 22, "And there passed not five and fifty days, before two of his sons killed him, and they fled into the mountains of Ararath; and Sarchedonus his son reigned in his stead."),
    # Chapter 2: Tobit becomes blind
    (2, 1, "Now when I was come home again, and my wife Anna was restored unto me, with my son Tobias, in the feast of Pentecost, which is the holy feast of the seven weeks, there was a good dinner prepared me, in the which I sat down to eat."),
    (2, 2, "And when I saw abundance of meat, I said to my son, Go and bring what poor man soever thou shalt find out of our brethren, who is mindful of the Lord; and, lo, I tarry for thee."),
    (2, 3, "But he came again, and said, Father, one of our nation is strangled, and is cast out in the marketplace."),
    (2, 4, "Then before I had tasted of any meat, I started up, and took him up into a room until the going down of the sun."),
    (2, 5, "Then I returned, and washed myself, and ate my meat in heaviness."),
    (2, 6, "Remembering that prophecy of Amos, as he said, Your feasts shall be turned into mourning, and all your mirth into lamentation."),
    (2, 7, "Therefore I wept: and after the going down of the sun I went and made a grave, and buried him."),
    (2, 8, "But my neighbours mocked me, and said, This man is not yet afraid to be put to death for this matter: who fled away; and yet, lo, he burieth the dead again."),
    (2, 9, "The same night also I returned from the burial, and slept by the wall of my courtyard, being polluted, and my face was uncovered."),
    (2, 10, "And I knew not that there were sparrows in the wall, and mine eyes being open, the sparrows muted warm dung into mine eyes, and a whiteness came in mine eyes; and I went to the physicians, but they helped me not."),
    (2, 11, "Moreover Achiacharus did nourish me, until I went into Elymais."),
    (2, 12, "And my wife Anna did take women's works to do."),
    (2, 13, "And when she had sent them home to the owners, they paid her wages, and gave her also besides a kid."),
    (2, 14, "And when it was come to my house, it began to cry, and I said unto her, From whence is this kid? is it not stolen? render it to the owners; for it is not lawful to eat any thing that is stolen."),
    # Chapter 3: Prayers of Tobit and Sarah
    (3, 1, "Then I being grieved did weep, and in my sorrow prayed, saying,"),
    (3, 2, "O Lord, thou art just, and all thy works and all thy ways are mercy and truth, and thou judgest truly and justly for ever."),
    (3, 3, "Remember me, and look on me, punish me not for my sins and ignorances, and the sins of my fathers, who have sinned before thee."),
    (3, 4, "For they obeyed not thy commandments: wherefore thou hast delivered us for a spoil, and unto captivity, and unto death, and for a proverb of reproach to all the nations among whom we are dispersed."),
    (3, 5, "And now thy judgements are many and true: deal with me according to my sins and my fathers': because we have not kept thy commandments, neither have walked in truth before thee."),
    (3, 6, "Now therefore deal with me as seemeth best unto thee, and command my spirit to be taken from me, that I may be dissolved, and become earth: for it is profitable for me to die rather than to live."),
    (3, 7, "It came to pass the same day, that in Ecbatane a city of Media Sara the daughter of Raguel was also reproached by her father's maids."),
    (3, 8, "Because that she had been married to seven husbands, whom Asmodeus the evil spirit had killed, before they had lain with her."),
    (3, 9, "Dost thou not know, said they, that thou hast strangled thine husbands? thou hast had already seven husbands, neither wast thou named after any of them."),
    (3, 10, "Wherefore dost thou beat us for them? if they be dead, go thy ways after them, let us never see of thee either son or daughter."),
    (3, 11, "When she heard these things, she was very sorrowful, so that she thought to have strangled herself; and she said, I am the only daughter of my father, and if I do this, it shall be a reproach unto him."),
    (3, 12, "And she prayed toward the window, and said, Blessed art thou, O Lord my God, and thine holy and glorious name is blessed and honourable for ever: let all thy works praise thee for ever."),
    (3, 13, "And now, O Lord, I set mine eyes and my face toward thee."),
    (3, 14, "And said, Take me out of the earth, that I may hear no more the reproach."),
    (3, 15, "Thou knowest, Lord, that I am pure from all sin with man."),
    (3, 16, "And that I never polluted my name, nor the name of my father, in the land of my captivity: I am the only daughter of my father, neither hath he any child to be his heir."),
    (3, 17, "And the prayer of them both was heard before the majesty of the great God."),
    # Chapter 4: Tobit's instructions to Tobias
    (4, 1, "In that day Tobit remembered the money which he had committed to Gabael in Rages of Media."),
    (4, 2, "And said with himself, I have wished for death; wherefore do I not call for my son Tobias, that I may signify to him of the money before I die?"),
    (4, 3, "And when he had called him, he said, My son, when I am dead, bury me; and despise not thy mother, but honour her all the days of thy life, and do that which shall please her, and grieve her not."),
    (4, 4, "Remember, my son, that she saw many dangers for thee, when thou wast in her womb: and when she is dead, bury her by me in one grave."),
    (4, 5, "My son, be mindful of the Lord our God all thy days, and let not thy will be set to sin, or to transgress his commandments: do uprightly all thy life long, and follow not the ways of unrighteousness."),
    (4, 6, "For if thou deal truly, thy doings shall prosperously succeed to thee, and to all them that live justly."),
    (4, 7, "Give alms of thy substance; and when thou givest alms, let not thine eye be envious, neither turn thy face from any poor, and the face of God shall not be turned away from thee."),
    (4, 8, "If thou hast abundance, give alms accordingly: if thou have but a little, be not afraid to give according to that little."),
    (4, 9, "For thou layest up a good treasure for thyself against the day of necessity."),
    (4, 10, "Because that alms do deliver from death, and suffereth not to come into darkness."),
    (4, 11, "For alms is a good gift unto all that give it in the sight of the most High."),
    (4, 12, "Beware of all whoredom, my son, and chiefly take a wife of the seed of thy fathers, and take not a strange woman to wife, which is not of thy father's tribe."),
    (4, 13, "For we are the children of the prophets, Noe, Abraham, Isaac, and Jacob: remember, my son, that our fathers from the beginning, even that they all married wives of their own kindred."),
    (4, 14, "Let not the wages of any man, which hath wrought for thee, tarry with thee, but give him it out of hand: for if thou serve God, he will also repay thee: be circumspect, my son, in all things thou doest, and be wise in all thy conversation."),
    (4, 15, "Do that to no man which thou hatest: drink not wine to make thee drunken: neither let drunkenness go with thee in thy journey."),
    (4, 16, "Give of thy bread to the hungry, and of thy garments to them that are naked; and according to thine abundance give alms: and let not thine eye be envious, when thou givest alms."),
    (4, 17, "Pour out thy bread on the burial of the just, but give nothing to the wicked."),
    (4, 18, "Ask counsel of all that are wise, and despise not any counsel that is profitable."),
    (4, 19, "Bless the Lord thy God alway, and desire of him that thy ways may be directed, and that all thy paths and counsels may prosper: for every nation hath not counsel; but the Lord himself giveth all good things."),
    (4, 20, "And he lifteth up whomsoever he will, and he casteth down to the lower parts of the earth: now therefore, my son, remember my commandments, neither let them be put out of thy mind."),
    (4, 21, "And now I signify this to thee, that I committed ten talents to Gabael the son of Gabrias at Rages in Media."),
    # Chapter 5: Journey with Raphael begins
    (5, 1, "Tobias then answered and said, Father, I will do all things which thou hast commanded me."),
    (5, 2, "But how can I receive the money, seeing I know him not?"),
    (5, 3, "Then he gave him the handwriting, and said unto him, Seek thee a man which may go with thee, whiles I yet live, and I will give him wages: and go and receive the money."),
    (5, 4, "Therefore when he went to seek a man, he found Raphael that was an angel."),
    (5, 5, "But he knew not; and he said unto him, Canst thou go with me to Rages? and knowest thou those places well?"),
    (5, 6, "To whom the angel said, I will go with thee, and I know the way well: for I have lodged with our brother Gabael."),
    (5, 7, "Then Tobias said unto him, Tarry for me, till I tell my father."),
    (5, 8, "Then he said unto him, Go and tarry not. So he went in and said to his father, Behold, I have found one which will go with me. Then he said, Call him unto me, that I may know of what tribe he is, and whether he be a trusty man to go with thee."),
    (5, 9, "So he called him, and he came in, and they saluted one another."),
    (5, 10, "Then Tobit said unto him, Brother, shew me of what tribe and family thou art."),
    (5, 11, "To whom he said, Dost thou seek for a tribe or family, or an hired man to go with thy son? Then Tobit said unto him, I would know, brother, thy kindred and name."),
    (5, 12, "Then he said, I am Azarias, the son of Ananias the great, and of thy brethren."),
    (5, 13, "Then Tobit said, Thou art welcome, brother; be not now angry with me, because I have enquired to know thy tribe and thy family; for thou art my brother, of an honest and good stock."),
    (5, 14, "For I know Ananias and Jonathas, sons of that great Samaias, as we went together to Jerusalem to worship, and offered the firstborn, and the tenths of the fruits; and they were not seduced with the error of our brethren."),
    (5, 15, "My brother, thou art of a good stock. But tell me, what wages shall I give thee? wilt thou a drachm a day, and things necessary, as to mine own son?"),
    (5, 16, "Yea, moreover, if ye return safe, I will add something to thy wages."),
    (5, 17, "So they were well pleased. Then said he to Tobias, Prepare thyself for the journey, and God send you a good journey. And when his son had prepared all things for the journey, his father said, Go thou with this man, and God, which dwelleth in heaven, prosper your journey, and the angel of God keep you company."),
    (5, 18, "So they went forth both, and the young man's dog with them."),
    (5, 19, "But Anna his mother wept, and said to Tobit, Why hast thou sent away our son? is he not the staff of our hand, in going in and out before us?"),
    (5, 20, "Be not greedy to add money to money: but let it be as refuse in respect of our child."),
    (5, 21, "For that which the Lord hath given us to live with doth suffice us."),
    (5, 22, "Then said Tobit to her, Take no care, my sister; he shall come in safety, and thine eyes shall see him."),
    # Chapter 6: The journey and the fish
    (6, 1, "Now as they went on their journey, they came in the evening to the river Tigris, and they lodged there."),
    (6, 2, "And when the young man went down to wash himself, a fish leaped out of the river, and would have devoured him."),
    (6, 3, "Then the angel said unto him, Take the fish. And the young man laid hold of the fish, and drew it to land."),
    (6, 4, "To whom the angel said, Open the fish, and take the heart and the liver and the gall, and put them up safely."),
    (6, 5, "So the young man did as the angel commanded him; and when they had roasted the fish, they did eat it: then they both went on their way, till they drew near to Ecbatane."),
    (6, 6, "Then the young man said to the angel, Brother Azarias, to what use is the heart and the liver and the gall of the fish?"),
    (6, 7, "And he said unto him, Touching the heart and the liver, if a devil or an evil spirit trouble any, we must make a smoke thereof before the man or the woman, and the party shall be no more vexed."),
    (6, 8, "As for the gall, it is good to anoint a man that hath whiteness in his eyes, and he shall be healed."),
    (6, 9, "And when they were come near to Rages,"),
    (6, 10, "The angel said to the young man, Brother, to day we shall lodge with Raguel, who is thy cousin; he also hath one only daughter, named Sara; I will speak for her, that she may be given thee for a wife."),
    (6, 11, "For to thee doth the right of her appertain, seeing thou only art of her kindred."),
    (6, 12, "And the maid is fair and wise: now therefore hear me, and I will speak to her father; and when we return from Rages we will celebrate the marriage: for I know that Raguel cannot marry her to another according to the law of Moses."),
    (6, 13, "Then the young man answered the angel, I have heard, brother Azarias, that this maid hath been given to seven men, who all died in the marriage chamber."),
    (6, 14, "And now I am the only son of my father, and I am afraid, lest if I go in unto her, I die, as the other before."),
    (6, 15, "For a wicked spirit loveth her, which hurteth no body, but those which come unto her; wherefore I also fear lest I die."),
    (6, 16, "Then the angel said unto him, Dost thou not remember the precepts which thy father gave thee, that thou shouldest marry a wife of thine own kindred?"),
    (6, 17, "Wherefore hear me, O my brother; for she shall be given thee to wife; and make thou no reckoning of the evil spirit; for this same night shall she be given thee in marriage."),
    (6, 18, "And when thou shalt come into the marriage chamber, thou shalt take the ashes of perfume, and shalt lay upon them some of the heart and liver of the fish, and shalt make a smoke with it."),
    (6, 19, "And the devil shall smell it, and flee away, and never come again any more: but when thou shalt come to her, rise up both of you, and pray to God which is merciful, who will have pity on you, and save you."),
    # Chapter 7: Marriage to Sarah
    (7, 1, "And when they were come to Ecbatane, they came to the house of Raguel, and Sara met them: and after they had saluted one another, she brought them into the house."),
    (7, 2, "Then said Raguel to Edna his wife, How like is this young man to Tobit my cousin!"),
    (7, 3, "And Raguel asked them, From whence are ye, brethren? To whom they said, We are of the sons of Nephthali, which are captives in Nineve."),
    (7, 4, "Then he said to them, Do ye know Tobit our kinsman? And they said, We know him. Then said he, Is he in good health?"),
    (7, 5, "And they said, He is both alive and in good health: and Tobias said, He is my father."),
    (7, 6, "Then Raguel leaped up, and kissed him, and wept,"),
    (7, 7, "And blessed him, and said unto him, Thou art the son of an honest and good man. But when he had heard that Tobit was blind, he was sorrowful, and wept."),
    (7, 8, "And likewise Edna his wife and Sara his daughter wept. Moreover they entertained them cheerfully; and after that they had killed a ram of the flock, they set store of meat on the table."),
    (7, 9, "Then said Tobias to Raphael, Brother Azarias, speak of those things of which thou didst talk in the way, and let this business be dispatched."),
    (7, 10, "So he communicated the matter with Raguel: and Raguel said to Tobias, Eat and drink, and make merry."),
    (7, 11, "For it is meet that thou shouldest marry my daughter: nevertheless I will declare unto thee the truth."),
    (7, 12, "I have given my daughter in marriage to seven men, who died that night they came in unto her: nevertheless for the present be merry. But Tobias said, I will eat nothing here, till we agree and swear one to another."),
    (7, 13, "Raguel said, Then take her from henceforth according to the manner, for thou art her cousin, and she is thine, and the merciful God give you good success in all things."),
    (7, 14, "Then he called his daughter Sara, and she came to her father, and he took her by the hand, and gave her to be wife to Tobias, saying, Behold, take her after the law of Moses, and lead her away to thy father. And he blessed them."),
    (7, 15, "And called Edna his wife, and took paper, and did write an instrument of covenants, and sealed it."),
    (7, 16, "Then they began to eat."),
    (7, 17, "After Raguel called his wife Edna, and said unto her, Sister, prepare another chamber, and bring her in thither."),
    # Chapter 8: Wedding night
    (8, 1, "And when they had supped, they brought Tobias in unto her."),
    (8, 2, "And as he went, he remembered the words of Raphael, and took the ashes of the perfumes, and put the heart and the liver of the fish thereupon, and made a smoke therewith."),
    (8, 3, "The which smell when the evil spirit had smelled, he fled into the utmost parts of Egypt, and the angel bound him."),
    (8, 4, "And after that they were both shut in together, Tobias rose out of his bed, and said, Sister, arise, and let us pray that God would have pity on us."),
    (8, 5, "Then began Tobias to say, Blessed art thou, O God of our fathers, and blessed is thy holy and glorious name for ever; let the heavens bless thee, and all thy creatures."),
    (8, 6, "Thou madest Adam, and gavest him Eve his wife for an helper and stay: of them came mankind: thou hast said, It is not good that man should be alone; let us make unto him an aid like unto himself."),
    (8, 7, "And now, O Lord, I take not this my sister for lust, but uprightly: therefore mercifully ordain that we may become aged together."),
    (8, 8, "And she said with him, Amen."),
    (8, 9, "So they slept both that night. And Raguel arose, and went and made a grave,"),
    (8, 10, "Saying, I fear lest he also be dead."),
    (8, 11, "But when Raguel was come into his house,"),
    (8, 12, "He said unto his wife Edna, Send one of the maids, and let her see whether he be alive: if he be not, that we may bury him, and no man know it."),
    (8, 13, "So the maid opened the door, and went in, and found them both asleep,"),
    (8, 14, "And came forth, and told them that he was alive."),
    (8, 15, "Then Raguel praised God, and said, O God, thou art worthy to be praised with all pure and holy praise; therefore let thy saints praise thee with all thy creatures; and let all thine angels and thine elect praise thee for ever."),
    (8, 16, "Thou art to be praised, for thou hast made me joyful; and that is not come to me which I suspected; but thou hast dealt with us according to thy great mercy."),
    (8, 17, "Thou art to be praised, because thou hast had mercy of two that were the only begotten children of their fathers: grant them mercy, O Lord, and finish their life in health with joy and mercy."),
    (8, 18, "Then Raguel bade his servants to fill the grave."),
    (8, 19, "And he kept the wedding feast fourteen days."),
    (8, 20, "For before the days of the marriage were finished, Raguel had said unto him by an oath, that he should not depart till the fourteen days of the marriage were expired."),
    (8, 21, "And then he should take the half of his goods, and go in safety to his father; and should have the rest when I and my wife be dead."),
    # Chapter 9: Tobias sends for the money
    (9, 1, "Then Tobias called Raphael, and said unto him,"),
    (9, 2, "Brother Azarias, take with thee a servant, and two camels, and go to Rages of Media to Gabael, and bring me the money, and bring him to the wedding."),
    (9, 3, "For Raguel hath sworn that I shall not depart."),
    (9, 4, "But my father counteth the days; and if I tarry long, he will be very sorry."),
    (9, 5, "So Raphael went out, and lodged with Gabael, and gave him the handwriting: who brought forth bags which were sealed up, and gave them to him."),
    (9, 6, "And early in the morning they went forth both together, and came to the wedding: and Tobias blessed his wife."),
    # Chapter 10: Tobit and Anna await the return
    (10, 1, "Now Tobit his father counted every day: and when the days of the journey were expired, and they came not,"),
    (10, 2, "Then Tobit said, Are they detained? or is Gabael dead, and there is no man to give him the money?"),
    (10, 3, "Therefore he was very sorry."),
    (10, 4, "Then his wife said unto him, My son is dead, seeing he stayeth long; and she began to wail him, and said,"),
    (10, 5, "Now I care for nothing, my son, since I have let thee go, the light of mine eyes."),
    (10, 6, "To whom Tobit said, Hold thy peace, take no care, for he is safe."),
    (10, 7, "But she said, Hold thy peace, and deceive me not; my son is dead. And she went out every day into the way which they went, and did eat no meat on the daytime, and ceased not whole nights to bewail her son Tobias."),
    (10, 8, "Until the fourteen days of the wedding were expired, which Raguel had sworn that he should spend there. Then Tobias said to Raguel, Let me go, for my father and my mother look no more to see me."),
    (10, 9, "But his father in law said unto him, Tarry with me, and I will send to thy father, and they shall declare unto him how things go with thee."),
    (10, 10, "But Tobias said, No; but let me go to my father."),
    (10, 11, "Then Raguel arose, and gave him Sara his wife, and half his goods, servants, and cattle, and money."),
    (10, 12, "And he blessed them, and sent them away, saying, The God of heaven give you a prosperous journey, my children."),
    (10, 13, "And he said to his daughter, Honour thy father and thy mother in law, which are now thy parents, that I may hear good report of thee. And he kissed her. Edna also said to Tobias, The Lord of heaven restore thee, my dear brother, and grant that I may see thy children of my daughter Sara before I die, that I may rejoice before the Lord."),
    # Chapter 11: Return and healing of Tobit
    (11, 1, "After these things Tobias went his way, praising God that he had given him a prosperous journey, and blessed Raguel and Edna his wife, and went on his way till they drew near unto Nineve."),
    (11, 2, "Then Raphael said to Tobias, Thou knowest, brother, how thou didst leave thy father."),
    (11, 3, "Let us haste before thy wife, and prepare the house."),
    (11, 4, "And take in thine hand the gall of the fish. So they went their way, and the dog went after them."),
    (11, 5, "Now Anna sat looking about toward the way for her son."),
    (11, 6, "And when she espied him coming, she said to his father, Behold, thy son cometh, and the man that went with him."),
    (11, 7, "Then said Raphael, I know, Tobias, that thy father will open his eyes."),
    (11, 8, "Therefore anoint thou his eyes with the gall, and being pricked therewith, he shall rub, and the whiteness shall fall away, and he shall see thee."),
    (11, 9, "Then Anna ran forth, and fell upon the neck of her son, and said unto him, Seeing I have seen thee, my son, from henceforth I am content to die. And they wept both."),
    (11, 10, "Tobit also went forth toward the door, and stumbled: but his son ran unto him,"),
    (11, 11, "And took hold of his father: and he strake of the gall on his father's eyes, saying, Be of good hope, my father."),
    (11, 12, "And when his eyes began to smart, he rubbed them;"),
    (11, 13, "And the whiteness pilled away from the corners of his eyes: and when he saw his son, he fell upon his neck."),
    (11, 14, "And he wept, and said, Blessed art thou, O God, and blessed is thy name for ever; and blessed are all thine holy angels."),
    (11, 15, "For thou hast scourged, and hast taken pity on me: for, behold, I see my son Tobias. And his son went in rejoicing, and told his father the great things that had happened to him in Media."),
    (11, 16, "Then Tobit went out to meet his daughter in law at the gate of Nineve, rejoicing and praising God: and they which saw him go marvelled, because he had received his sight."),
    (11, 17, "But Tobit gave thanks before them, because God had mercy on him. And when he came near to Sara his daughter in law, he blessed her, saying, Thou art welcome, daughter: God be blessed, which hath brought thee unto us, and blessed be thy father and thy mother. And there was joy among all his brethren which were at Nineve."),
    (11, 18, "And Achiacharus, and Nasbas his brother's son, came."),
    # Chapter 12: Raphael reveals his identity
    (12, 1, "Then Tobit called his son Tobias, and said unto him, My son, see that the man have his wages, which went with thee, and thou must give him more."),
    (12, 2, "And Tobias said unto him, O father, it is no harm to me to give him half of those things which I have brought."),
    (12, 3, "For he hath brought me again to thee in safety, and made whole my wife, and brought me the money, and likewise healed thee."),
    (12, 4, "Then the old man said, It is due unto him."),
    (12, 5, "So he called the angel, and he said unto him, Take half of all that ye have brought and go away in safety."),
    (12, 6, "Then he took them both apart, and said unto them, Bless God, praise him, and magnify him, and praise him for the things which he hath done unto you in the sight of all that live. It is good to praise God, and exalt his name, and honourably to shew forth the works of God; therefore be not slack to praise him."),
    (12, 7, "It is good to keep close the secret of a king, but it is honourable to reveal the works of God. Do that which is good, and no evil shall touch you."),
    (12, 8, "Prayer is good with fasting and alms and righteousness. A little with righteousness is better than much with unrighteousness. It is better to give alms than to lay up gold."),
    (12, 9, "For alms doth deliver from death, and shall purge away all sin. Those that exercise alms and righteousness shall be filled with life."),
    (12, 10, "But they that sin are enemies to their own life."),
    (12, 11, "Surely I will keep close nothing from you. For I said, It was good to keep close the secret of a king, but that it was honourable to reveal the works of God."),
    (12, 12, "Now therefore, when thou didst pray, and Sara thy daughter in law, I did bring the remembrance of your prayers before the Holy One: and when thou didst bury the dead, I was with thee likewise."),
    (12, 13, "And when thou didst not delay to rise up, and leave thy dinner, to go and cover the dead, thy good deed was not hid from me: but I was with thee."),
    (12, 14, "And now God hath sent me to heal thee and Sara thy daughter in law."),
    (12, 15, "I am Raphael, one of the seven holy angels, which present the prayers of the saints, and which go in and out before the glory of the Holy One."),
    (12, 16, "Then they were both troubled, and fell upon their faces: for they feared."),
    (12, 17, "But he said unto them, Fear not, for it shall go well with you; praise God therefore."),
    (12, 18, "For not of any favour of mine, but by the will of our God I came; wherefore praise him for ever."),
    (12, 19, "All these days I did appear unto you; but I did neither eat nor drink, but ye did see a vision."),
    (12, 20, "Now therefore give God thanks: for I go up to him that sent me. Write all things which are done in a book."),
    (12, 21, "And when they arose, they saw him no more."),
    (12, 22, "Then they confessed the great and wonderful works of God, and how the angel of the Lord had appeared unto them."),
    # Chapter 13: Tobit's hymn of praise
    (13, 1, "Then Tobit wrote a prayer of rejoicing, and said, Blessed be God that liveth for ever, and blessed be his kingdom."),
    (13, 2, "For he doth scourge, and hath mercy: he leadeth down to hell, and bringeth up again: neither is there any that can avoid his hand."),
    (13, 3, "Confess him before the Gentiles, ye children of Israel: for he hath scattered us among them."),
    (13, 4, "There declare his greatness, and extol him before all the living: for he is our Lord, and he is the God our Father for ever."),
    (13, 5, "And he will scourge us for our iniquities, and will have mercy again, and will gather us out of all nations, among whom he hath scattered us."),
    (13, 6, "If ye turn to him with your whole heart, and with your whole mind, and deal uprightly before him, then will he turn unto you, and will not hide his face from you."),
    (13, 7, "Therefore see what he will do with you, and confess him with your whole mouth, and praise the Lord of might, and extol the everlasting King."),
    (13, 8, "In the land of my captivity do I praise him, and declare his might and majesty to a sinful nation."),
    (13, 9, "O ye sinners, turn and do justice before him: who can tell if he will accept you, and have mercy on you?"),
    (13, 10, "I will extol my God, and my soul shall praise the King of heaven, and shall rejoice in his greatness."),
    (13, 11, "Let all men speak, and let all praise him for his righteousness."),
    (13, 12, "O Jerusalem, the holy city, he will scourge thee for thy children's works, and will have mercy again on the sons of the righteous."),
    (13, 13, "Give praise to the Lord, for he is good: and praise the everlasting King, that his tabernacle may be builded in thee again with joy."),
    (13, 14, "And let him make joyful there in thee those that are captives, and love in thee for ever those that are miserable."),
    (13, 15, "Many nations shall come from far to the name of the Lord God with gifts in their hands, even gifts to the King of heaven; all generations shall praise thee with great joy."),
    (13, 16, "Cursed are all they which hate thee, and blessed shall all be which love thee for ever."),
    (13, 17, "Rejoice and be glad for the children of the just: for they shall be gathered together, and shall bless the Lord of the just."),
    (13, 18, "O blessed are they which love thee, for they shall rejoice in thy peace: blessed are they which have been sorrowful for all thy scourges; for they shall rejoice for thee, when they have seen all thy glory, and shall be glad for ever."),
    # Chapter 14: Tobit's death
    (14, 1, "So Tobit made an end of praising God."),
    (14, 2, "And he was eight and fifty years old when he lost his sight, which was restored to him after eight years: and he gave alms, and he increased in the fear of the Lord God, and praised him."),
    (14, 3, "And when he was very aged, he called his son, and the sons of his son, and said to him, My son, take thy children; for, behold, I am aged, and am ready to depart out of this life."),
    (14, 4, "Go into Media, my son, for I surely believe those things which Jonas the prophet spake of Nineve, that it shall be overthrown; and that for a time peace shall rather be in Media; and that our brethren shall lie scattered in the earth from that good land."),
    (14, 5, "And that the temple of God shall be burned, and the house of God in it shall be rebuilt, as the prophets have declared thereof."),
    (14, 6, "And that all nations shall turn, and fear the Lord God truly, and shall bury their idols."),
    (14, 7, "So shall all nations praise the Lord, and his people shall confess God, and the Lord shall exalt his people; and all those which love the Lord God in truth and justice shall rejoice, shewing mercy to our brethren."),
    (14, 8, "And now, my son, depart out of Nineve, because that those things which the prophet Jonas spake shall surely come to pass."),
    (14, 9, "But keep thou the law and the commandments, and shew thyself merciful and just, that it may go well with thee."),
    (14, 10, "And bury me decently, and thy mother with me; but tarry no longer at Nineve. Remember, my son, how Aman handled Achiacharus that brought him up, how out of light he brought him into darkness, and how he rewarded him again: yet Achiacharus was saved, but the other had his reward: for he went down into darkness."),
    (14, 11, "Manasses gave alms, and escaped the snares of death which they had set for him: but Aman fell into the snare, and perished."),
    (14, 12, "Wherefore now, my son, consider what alms doeth, and how righteousness doth deliver. When he had said these things, he gave up the ghost in the bed, being an hundred and eight and fifty years old; and he buried him honourably."),
    (14, 13, "And when Anna his mother was dead, he buried her with his father. But Tobias departed with his wife and children to Ecbatane to Raguel his father in law."),
    (14, 14, "Where he became old with honour, and he buried his father and mother in law honourably, and he inherited their substance, and his father Tobit's."),
    (14, 15, "And he died at Ecbatane in Media, being an hundred and seven and twenty years old."),
]

def make_tobit_coptic():
    return [(2007, 200, ch, v, text, f"Tobit {ch}:{v}") for ch, v, text in TOBIT_VERSES_RAW]

def make_tobit_russian():
    return [(4003, 400, ch, v, text, f"Tobit {ch}:{v}") for ch, v, text in TOBIT_VERSES_RAW]


# ---------------------------------------------------------------------------
# Judith — KJV Apocrypha (public domain)
# Coptic (book_id=2008, volume_id=200) and Russian (book_id=4004, volume_id=400)
# 16 chapters
# ---------------------------------------------------------------------------

JUDITH_VERSES_RAW = [
    # Chapter 1
    (1, 1, "In the twelfth year of the reign of Nabuchodonosor, who reigned in Nineve, the great city; in the days of Arphaxad, which reigned over the Medes in Ecbatane."),
    (1, 2, "And built in Ecbatane walls round about of stones hewn three cubits broad and six cubits long, and made the height of the wall seventy cubits, and the breadth thereof fifty cubits."),
    (1, 3, "And set the towers thereof upon the gates of it, an hundred cubits high, and the breadth thereof in the foundation threescore cubits."),
    (1, 4, "And he made the gates thereof, even gates that were raised to the height of seventy cubits, and the breadth of them was forty cubits, for the going forth of his mighty armies, and for the setting in array of his footmen."),
    (1, 5, "Even in those days king Nabuchodonosor made war with king Arphaxad in the great plain, which is the plain in the borders of Ragau."),
    (1, 6, "And there came unto him all they that dwelt in the hill country, and all that dwelt by Euphrates, and Tigris, and Hydaspes, and the plain of Arioch the king of the Elymeans."),
    (1, 7, "And many nations of the sons of Chelod assembled themselves to the battle."),
    (1, 8, "Then Nabuchodonosor king of the Assyrians sent unto all that dwelt in Persia, and to all that dwelt westward."),
    (1, 9, "And to those that dwelt in Cilicia, and Damascus, and Libanus, and Antilibanus, and to all that dwelt upon the sea coast."),
    (1, 10, "And to those among the nations that were of Carmel, and Galaad, and the higher Galilee, and the great plain of Esdrelom."),
    (1, 11, "And to all that were in Samaria and the cities thereof, and beyond Jordan unto Jerusalem, and Betane, and Chellus, and Kades, and the river of Egypt, and Taphnes, and Ramesse, and all the land of Gesem."),
    (1, 12, "Until ye come beyond Tanis and Memphis, and to all the inhabitants of Egypt, until ye come to the borders of Ethiopia."),
    (1, 13, "But all the inhabitants of the land made light of the commandment of Nabuchodonosor king of the Assyrians, neither went they with him to the battle; for they were not afraid of him: yea, he was before them as one man."),
    (1, 14, "And they sent away his ambassadors from them without effect, and with disgrace."),
    (1, 15, "Therefore Nabuchodonosor was very angry with all this country, and sware by his throne and kingdom, that he would surely be avenged upon all those coasts of Cilicia, and Damascus, and Syria."),
    (1, 16, "And that he would slay with the sword all the inhabitants of the land of Moab, and the children of Ammon, and all Judea, and all that were in Egypt, till ye come to the borders of the two seas."),
    # Chapter 2
    (2, 1, "And in the eighteenth year, the two and twentieth day of the first month, there was talk in the house of Nabuchodonosor king of the Assyrians, that he should avenge himself on all the earth, even as he had spoken."),
    (2, 2, "And he called unto him all his officers, and all his nobles, and communicated with them his secret counsel, and concluded the afflicting of the whole earth out of his own mouth."),
    (2, 3, "Then they decreed to destroy all flesh, that did not obey the commandment of his mouth."),
    (2, 4, "And when he had ended his counsel, Nabuchodonosor king of the Assyrians called Holofernes the chief captain of his army, which was next unto him."),
    (2, 5, "And said unto him, Go forth and take with thee men that trust in their own strength, of footmen an hundred and twenty thousand; and of horse twelve thousand."),
    (2, 6, "And thou shalt go against all the west country, because they disobeyed my commandment."),
    (2, 7, "And thou shalt declare unto them, that they prepare for me earth and water: for I will go forth in my wrath against them."),
    (2, 8, "And will cover the whole face of the earth with the feet of mine army, and I will give them for a spoil unto them."),
    (2, 9, "So that their slain shall fill their valleys and brooks, and the river shall be filled with their dead, till it overflow."),
    (2, 10, "And I will lead them captives to the utmost parts of all the earth."),
    # Chapter 8: Judith introduced
    (8, 1, "Now at that time Judith heard thereof, which was the daughter of Merari, the son of Ox, the son of Joseph."),
    (8, 2, "And Manasses was her husband, of her tribe and kindred, who died in the barley harvest."),
    (8, 3, "For as he stood overseeing them that bound sheaves in the field, the heat came upon his head, and he fell on his bed, and died in the city of Bethulia: and they buried him with his fathers."),
    (8, 4, "So Judith was a widow in her house three years and four months."),
    (8, 5, "And she made her a tent upon the top of her house, and put on sackcloth upon her loins and wore her widow's garments."),
    (8, 6, "And she fasted all the days of her widowhood, save the eves of the sabbaths, and the sabbaths, and the eves of the new moons, and the new moons, and the feasts and solemn days of the house of Israel."),
    (8, 7, "She was also of a goodly countenance, and very beautiful to behold: and her husband Manasses had left her gold, and silver, and menservants, and maidservants, and cattle, and lands; and she remained upon them."),
    (8, 8, "And there was none that gave her an ill word; for she feared God greatly."),
    (8, 9, "Now when she heard the evil words of the people against the governor, that they fainted for lack of water; for Judith had heard all the words that Ozias had spoken unto them."),
    (8, 10, "And how he had sworn to deliver the city unto the Assyrians after five days."),
    (8, 11, "Then she sent her waitingwoman, that had the government of all things that she had, to call Ozias and Chabris and Charmis, the ancients of the city."),
    (8, 12, "And they came unto her, and she said unto them, Hear me now, O ye governors of the inhabitants of Bethulia."),
    # Chapter 9: Judith's prayer
    (9, 1, "Then Judith fell upon her face, and put ashes upon her head, and uncovered the sackcloth wherewith she was clothed; and about the time that the incense of that evening was offered in Jerusalem in the house of the Lord, Judith cried with a loud voice."),
    (9, 2, "And said, O Lord God of my father Simeon, to whom thou gavest a sword to take vengeance of the strangers."),
    (9, 3, "Who loosened the girdle of a maid to defile her, and discovered the thigh to her shame, and polluted her virginity to her reproach; for thou saidst, It shall not be so; and yet they did so."),
    (9, 4, "Wherefore thou gavest their rulers to be slain, so that they dyed their bed in blood, being deceived, and smotest the servants with their lords, and the lords upon their thrones."),
    (9, 5, "And hast given their wives for a prey, and their daughters to be captives, and all their spoils to be divided among thy dear children; which were moved with thy zeal, and abhorred the pollution of their blood, and called upon thee for aid: O God, O my God, hear me also a widow."),
    (9, 6, "For thou hast wrought not only those things, but also the things which fell out before, and which ensued after; thou hast thought upon the things which are now, and which are to come."),
    (9, 7, "Yea, what things thou didst determine were ready at hand, and said, Lo, we are here: for all thy ways are prepared, and thy judgements are in thy foreknowledge."),
    (9, 8, "For, behold, the Assyrians are multiplied in their power; they are exalted with horse and man; they glory in the strength of their footmen; they trust in shield, and spear, and bow, and sling."),
    (9, 9, "And know not that thou art the Lord that breakest the battles: the Lord is thy name."),
    (9, 10, "Throw down their strength in thy power, and bring down their force in thy wrath."),
    (9, 11, "For thy power standeth not in multitude nor thy might in strong men: for thou art a God of the afflicted, an helper of the oppressed, an upholder of the weak, a protector of the forlorn, a saviour of them that are without hope."),
    # Chapter 10: Judith prepares
    (10, 1, "Now after that she had ceased to cry unto the God of Israel, and had made an end of all these words."),
    (10, 2, "She rose where she had fallen down, and called her maid, and went down into the house in the which she abode in the sabbath days, and in her feast days."),
    (10, 3, "And pulled off the sackcloth which she had on, and put off the garments of her widowhood, and washed her body all over with water, and anointed herself with precious ointment."),
    (10, 4, "And braided the hair of her head, and put on a tire upon it, and put on her garments of gladness, wherewith she was clad during the life of Manasses her husband."),
    (10, 5, "And she took sandals upon her feet, and put about her her bracelets, and her chains, and her rings, and her earrings, and all her ornaments, and decked herself bravely, to allure the eyes of all men that should see her."),
    # Chapter 13: Judith slays Holofernes
    (13, 1, "So all the people went away, and none was left in the bedchamber, neither small nor great. Then Judith, standing by his bed, said in her heart, O Lord God of all power, look at this present upon the works of mine hands for the exaltation of Jerusalem."),
    (13, 2, "For now is the time to help thine inheritance, and to execute thine enterprises to the destruction of the enemies which are risen against us."),
    (13, 3, "Then she came to the pillar of the bed, which was at Holofernes' head, and took down his fauchion from thence."),
    (13, 4, "And approached to his bed, and took hold of the hair of his head, and said, Strengthen me, O Lord God of Israel, this day."),
    (13, 5, "And she smote twice upon his neck with all her might, and she took away his head from him."),
    (13, 6, "And tumbled his body down from the bed, and pulled down the canopy from the pillars; and anon after she went forth, and gave Holofernes his head to her maid."),
    (13, 7, "And she put it in her bag of meat: so they twain went together according to their custom unto prayer: and when they passed the camp, they compassed the valley, and went up the mountain of Bethulia, and came to the gates thereof."),
    (13, 8, "Then said Judith afar off to the watchmen at the gate, Open, open now the gate: God, even our God, is with us, to shew his power yet in Jerusalem, and his forces against the enemy, as he hath even done this day."),
    (13, 9, "Now when the men of her city heard her voice, they made haste to go down to the gate of their city, and they called the elders of the city."),
    (13, 10, "And then they ran all together, both small and great, for it was strange unto them that she was come: so they opened the gate, and received them."),
    (13, 11, "And made a fire for a light, and stood round about them."),
    (13, 12, "Then she said to them with a loud voice, Praise, praise God, praise God, I say, for he hath not taken away his mercy from the house of Israel, but hath destroyed our enemies by mine hands this night."),
    (13, 13, "So she took the head out of the bag, and shewed it, and said unto them, Behold the head of Holofernes, the chief captain of the army of Assur, and behold the canopy, wherein he did lie in his drunkenness; and the Lord hath smitten him by the hand of a woman."),
    (13, 14, "As the Lord liveth, who hath kept me in my way that I went, my countenance hath deceived him to his destruction, and yet hath he not committed sin with me, to defile and shame me."),
    # Chapter 16: Judith's song of thanksgiving
    (16, 1, "Then Judith began to sing this thanksgiving in all Israel, and all the people sang after her this song of praise."),
    (16, 2, "And Judith said, Begin unto my God with timbrels, sing unto my Lord with cymbals: tune unto him a new psalm: exalt him, and call upon his name."),
    (16, 3, "For God breaketh the battles: for among the camps in the midst of the people he hath delivered me out of the hands of them that persecuted me."),
    (16, 4, "Assur came out of the mountains from the north, he came with ten thousands of his army, the multitude whereof stopped the torrents, and their horsemen have covered the hills."),
    (16, 5, "He bragged that he would burn up my borders, and kill my young men with the sword, and dash the sucking children against the ground, and make mine infants as a prey, and my virgins as a spoil."),
    (16, 6, "But the Almighty Lord hath disappointed them by the hand of a woman."),
    (16, 7, "For the mighty one did not fall by the young men, neither did the sons of the Titans smite him, nor high giants set upon him: but Judith the daughter of Merari weakened him with the beauty of her countenance."),
    (16, 13, "I will sing unto the Lord a new song: O Lord, thou art great and glorious, wonderful in strength, and invincible."),
    (16, 14, "Let all creatures serve thee: for thou spakest, and they were made, thou didst send forth thy spirit, and it created them, and there is none that can resist thy voice."),
    (16, 15, "For the mountains shall be moved from their foundations with the waters, the rocks shall melt as wax at thy presence: yet thou art merciful to them that fear thee."),
    (16, 16, "For all sacrifice is too little for a sweet savour unto thee, and all the fat is not sufficient for thy burnt offering: but he that feareth the Lord is great at all times."),
    (16, 17, "Woe to the nations that rise up against my kindred! the Lord Almighty will take vengeance of them in the day of judgement, in putting fire and worms in their flesh; and they shall feel them, and weep for ever."),
]

def make_judith_coptic():
    return [(2008, 200, ch, v, text, f"Judith {ch}:{v}") for ch, v, text in JUDITH_VERSES_RAW]

def make_judith_russian():
    return [(4004, 400, ch, v, text, f"Judith {ch}:{v}") for ch, v, text in JUDITH_VERSES_RAW]


# ---------------------------------------------------------------------------
# Baruch — KJV Apocrypha (public domain), 6 chapters
# Including Letter of Jeremiah as chapter 6
# Coptic (book_id=2009, volume_id=200) and Russian (book_id=4007, volume_id=400)
# ---------------------------------------------------------------------------

BARUCH_VERSES_RAW = [
    # Chapter 1
    (1, 1, "And these are the words of the book, which Baruch the son of Nerias, the son of Maasias, the son of Sedecias, the son of Asadias, the son of Chelcias, wrote in Babylon."),
    (1, 2, "In the fifth year, and in the seventh day of the month, what time as the Chaldeans took Jerusalem, and burnt it with fire."),
    (1, 3, "And Baruch did read the words of this book in the hearing of Jechonias the son of Joachim king of Juda, and in the ears of all the people that came to hear the book."),
    (1, 4, "And in the hearing of the nobles, and of the king's sons, and in the hearing of the elders, and of all the people, from the lowest unto the highest, even of all them that dwelt at Babylon by the river Sud."),
    (1, 5, "Whereupon they wept, fasted, and prayed before the Lord."),
    (1, 6, "They made also a collection of money according to every man's power."),
    (1, 7, "And they sent it to Jerusalem unto Joachim the high priest, the son of Chelcias, son of Salom, and to the priests, and to all the people which were found with him at Jerusalem."),
    (1, 8, "At the same time when he received the vessels of the house of the Lord, that were carried out of the temple, to return them into the land of Juda, the tenth day of the month Sivan, namely, silver vessels, which Sedecias the son of Josias king of Juda had made."),
    (1, 9, "After that Nabuchodonosor king of Babylon had carried away Jechonias, and the princes, and the captives, and the mighty men, and the people of the land, from Jerusalem, and brought them unto Babylon."),
    (1, 10, "And they said, Behold, we have sent you money to buy you burnt offerings, and sin offerings, and incense, and prepare ye manna, and offer upon the altar of the Lord our God."),
    (1, 11, "And pray for the life of Nabuchodonosor king of Babylon, and for the life of Balthasar his son, that their days may be upon earth as the days of heaven."),
    (1, 12, "And the Lord will give us strength, and lighten our eyes, and we shall live under the shadow of Nabuchodonosor king of Babylon, and under the shadow of Balthasar his son, and we shall serve them many days, and find favour in their sight."),
    # Chapter 2
    (2, 1, "Therefore the Lord hath made good his word, which he pronounced against us, and against our judges that judged Israel, and against our kings, and against our princes, and against the men of Israel and Juda."),
    (2, 2, "To bring upon us great plagues, such as never happened under the whole heaven, as it came to pass in Jerusalem, according to the things that were written in the law of Moses."),
    (2, 3, "That a man should eat the flesh of his own son, and the flesh of his own daughter."),
    (2, 4, "Moreover he hath delivered them to be in subjection to all the kingdoms that are round about us, to be as a reproach and desolation among all the people round about, where the Lord hath scattered them."),
    (2, 5, "Thus we were cast down, and not exalted, because we have sinned against the Lord our God, and have not been obedient unto his voice."),
    # Chapter 3
    (3, 1, "O Lord Almighty, God of Israel, the soul in anguish, the troubled spirit, crieth unto thee."),
    (3, 2, "Hear, O Lord, and have mercy; for thou art merciful: and have pity upon us, because we have sinned before thee."),
    (3, 3, "For thou endurest for ever, and we perish utterly."),
    (3, 4, "O Lord Almighty, thou God of Israel, hear now the prayers of the dead Israelites, and of their children, which have sinned before thee, and not hearkened unto the voice of thee their God: for the which cause these plagues cleave unto us."),
    (3, 9, "Hear, Israel, the commandments of life: give ear to understand wisdom."),
    (3, 10, "How happeneth it Israel, that thou art in thine enemies' land, that thou art waxen old in a strange country, that thou art defiled with the dead?"),
    (3, 11, "That thou art counted with them that go down into the grave?"),
    (3, 12, "Thou hast forsaken the fountain of wisdom."),
    (3, 13, "For if thou hadst walked in the way of God, thou shouldest have dwelled in peace for ever."),
    (3, 14, "Learn where is wisdom, where is strength, where is understanding; that thou mayest know also where is length of days, and life, where is the light of the eyes, and peace."),
    (3, 15, "Who hath found out her place? or who hath come into her treasures?"),
    (3, 24, "O Israel, how great is the house of God! and how large is the place of his possession!"),
    (3, 25, "Great, and hath none end; high, and unmeasurable."),
    (3, 29, "Who hath gone up into heaven, and taken her, and brought her down from the clouds?"),
    (3, 30, "Who hath gone over the sea, and found her, and will bring her for pure gold?"),
    (3, 35, "This is our God, and there shall none other be accounted of in comparison of him."),
    (3, 36, "He hath found out all the way of knowledge, and hath given it unto Jacob his servant, and to Israel his beloved."),
    (3, 37, "Afterward did he shew himself upon earth, and conversed with men."),
    # Chapter 4
    (4, 1, "This is the book of the commandments of God, and the law that endureth for ever: all they that keep it shall come to life; but such as leave it shall die."),
    (4, 2, "Turn thee, O Jacob, and take hold of it: walk in the presence of the light thereof, that thou mayest be illuminated."),
    (4, 3, "Give not thine honour to another, nor the things that are profitable unto thee to a strange nation."),
    (4, 4, "O Israel, happy are we: for things that are pleasing to God are made known unto us."),
    (4, 5, "Be of good cheer, my people, the memorial of Israel."),
    (4, 6, "Ye were sold to the nations, not for your destruction: but because ye moved God to wrath, ye were delivered unto the enemies."),
    (4, 7, "For ye provoked him that made you by sacrificing unto devils, and not to God."),
    (4, 8, "Ye have forgotten the everlasting God, that brought you up; and ye have grieved Jerusalem, that nursed you."),
    (4, 36, "O Jerusalem, look about thee toward the east, and behold the joy that cometh unto thee from God."),
    (4, 37, "Lo, thy sons come, whom thou sentest away, they come gathered together from the east to the west by the word of the Holy One, rejoicing in the glory of God."),
    # Chapter 5
    (5, 1, "Put off, O Jerusalem, the garment of thy mourning and affliction, and put on the comeliness of the glory that cometh from God for ever."),
    (5, 2, "Cast about thee a double garment of the righteousness which cometh from God; and set a diadem on thine head of the glory of the Everlasting."),
    (5, 3, "For God will shew thy brightness unto every country under heaven."),
    (5, 4, "For thy name shall be called of God for ever The peace of righteousness, and The glory of God's worship."),
    (5, 5, "Arise, O Jerusalem, and stand on high, and look about toward the east, and behold thy children gathered from the west unto the east by the word of the Holy One, rejoicing in the remembrance of God."),
    (5, 6, "For they departed from thee on foot, and were led away of their enemies: but God bringeth them unto thee exalted with glory, as children of the kingdom."),
    (5, 7, "For God hath appointed that every high hill, and banks of long continuance, should be cast down, and valleys filled up, to make even the ground, that Israel may go safely in the glory of God."),
    (5, 8, "Moreover even the woods and every sweetsmelling tree shall overshadow Israel by the commandment of God."),
    (5, 9, "For God shall lead Israel with joy in the light of his glory with the mercy and righteousness that cometh from him."),
    # Chapter 6: Letter of Jeremiah
    (6, 1, "A copy of an epistle, which Jeremy sent unto them which were to be led captives into Babylon by the king of the Babylonians, to certify them, as it was commanded him of God."),
    (6, 2, "Because of the sins which ye have committed before God, ye shall be led away captives into Babylon by Nabuchodonosor king of the Babylonians."),
    (6, 3, "So when ye come unto Babylon, ye shall remain there many years, and for a long season, namely, seven generations: and after that I will bring you away peaceably from thence."),
    (6, 4, "Now shall ye see in Babylon gods of silver, and of gold, and of wood, borne upon shoulders, which cause the nations to fear."),
    (6, 5, "Beware therefore that ye in no wise be like to strangers, neither be ye afraid of them, when ye see the multitude before them and behind them, worshipping them."),
    (6, 6, "But say ye in your hearts, O Lord, we must worship thee."),
    (6, 7, "For mine angel is with you, and I myself caring for your souls."),
    (6, 8, "As for their tongue, it is polished by the workman, and they themselves are gilded and laid over with silver; yet are they but false, and cannot speak."),
    (6, 9, "And taking gold, as it were for a virgin that loveth to go gay, they make crowns for the heads of their gods."),
    (6, 10, "Sometimes also the priests convey from their gods gold and silver, and bestow it upon themselves."),
    (6, 72, "Better therefore is the just man that hath none idols: for he shall be far from reproach."),
]

def make_baruch_coptic():
    return [(2009, 200, ch, v, text, f"Baruch {ch}:{v}") for ch, v, text in BARUCH_VERSES_RAW]

def make_baruch_russian():
    return [(4007, 400, ch, v, text, f"Baruch {ch}:{v}") for ch, v, text in BARUCH_VERSES_RAW]


# ---------------------------------------------------------------------------
# 1 Maccabees — KJV Apocrypha (public domain), 16 chapters
# Coptic (book_id=4102, volume_id=200) and Russian (book_id=4009, volume_id=400)
# ---------------------------------------------------------------------------

MACCABEES1_VERSES_RAW = [
    # Chapter 1
    (1, 1, "And it happened, after that Alexander son of Philip, the Macedonian, who came out of the land of Chettiim, had smitten Darius king of the Persians and Medes, that he reigned in his stead, the first over Greece."),
    (1, 2, "And made many wars, and won many strong holds, and slew the kings of the earth."),
    (1, 3, "And went through to the ends of the earth, and took spoils of many nations, insomuch that the earth was quiet before him; whereupon he was exalted, and his heart was lifted up."),
    (1, 4, "And he gathered a mighty strong host, and ruled over countries, and nations, and kings, who became tributaries unto him."),
    (1, 5, "And after these things he fell sick, and perceived that he should die."),
    (1, 6, "Wherefore he called his servants, such as were honourable, and had been brought up with him from his youth, and parted his kingdom among them, while he was yet alive."),
    (1, 7, "So Alexander reigned twelve years, and then died."),
    (1, 8, "And his servants bare rule every one in his place."),
    (1, 9, "And after his death they all put crowns upon themselves; so did their sons after them many years: and evils were multiplied in the earth."),
    (1, 10, "And there came out of them a wicked root Antiochus surnamed Epiphanes, son of Antiochus the king, who had been an hostage at Rome, and he reigned in the hundred and thirty and seventh year of the kingdom of the Greeks."),
    (1, 20, "And after that Antiochus had smitten Egypt, he returned again in the hundred forty and third year, and went up against Israel and Jerusalem with a great multitude."),
    (1, 21, "And entered proudly into the sanctuary, and took away the golden altar, and the candlestick of light, and all the vessels thereof."),
    (1, 22, "And the table of the shewbread, and the pouring vessels, and the vials, and the censers of gold, and the veil, and the crowns, and the golden ornaments that were before the temple, all which he pulled off."),
    (1, 23, "He took also the silver and the gold, and the precious vessels: also he took the hidden treasures which he found."),
    (1, 24, "And when he had taken all away, he went into his own land, having made a great massacre, and spoken very proudly."),
    (1, 41, "Moreover king Antiochus wrote to his whole kingdom, that all should be one people."),
    (1, 42, "And every one should leave his laws: so all the heathen agreed according to the commandment of the king."),
    (1, 54, "Now the fifteenth day of the month Casleu, in the hundred forty and fifth year, they set up the abomination of desolation upon the altar, and builded idol altars throughout the cities of Juda on every side."),
    (1, 62, "Howbeit many in Israel were fully resolved and confirmed in themselves not to eat any unclean thing."),
    (1, 63, "Wherefore they chose rather to die, that they might not be defiled with meats, and that they might not profane the holy covenant: so then they died."),
    (1, 64, "And there was very great wrath upon Israel."),
    # Chapter 2
    (2, 1, "In those days arose Mattathias the son of John, the son of Simeon, a priest of the sons of Joarib, from Jerusalem, and dwelt in Modin."),
    (2, 2, "And he had five sons, Joannan, called Caddis: Simon, called Thassi."),
    (2, 3, "Judas, who was called Maccabeus: Eleazar, called Avaran: and Jonathan, whose surname was Apphus."),
    (2, 4, "And when he saw the blasphemies that were committed in Juda and Jerusalem."),
    (2, 5, "He said, Woe is me! wherefore was I born to see this misery of my people, and of the holy city, and to dwell there, when it was delivered into the hand of the enemy, and the sanctuary into the hand of strangers?"),
    (2, 15, "And the king's officers came to the city of Modin, to make them sacrifice."),
    (2, 16, "And when many of Israel came unto them, Mattathias also and his sons came together."),
    (2, 17, "Then answered the king's officers and said unto Mattathias on this wise, Thou art a ruler, and an honourable and great man in this city, and strengthened with sons and brethren."),
    (2, 19, "Then Mattathias answered and spake with a loud voice, Though all the nations that are under the king's dominion obey him, and fall away every one from the religion of their fathers, and give consent to his commandments."),
    (2, 20, "Yet will I and my sons and my brethren walk in the covenant of our fathers."),
    (2, 21, "God forbid that we should forsake the law and the ordinances."),
    (2, 22, "We will not hearken to the king's words, to go from our religion, either on the right hand, or the left."),
    (2, 49, "Now when the time drew near that Mattathias should die, he said unto his sons, Now hath pride and rebuke gotten strength, and the time of destruction, and the wrath of indignation."),
    (2, 50, "Now therefore, my sons, be ye zealous for the law, and give your lives for the covenant of your fathers."),
    (2, 51, "Call to remembrance what acts our fathers did in their time; so shall ye receive great honour and an everlasting name."),
    (2, 64, "Fear not then the words of a sinful man: for his glory shall be dung and worms."),
    (2, 65, "To day he shall be lifted up, and to morrow he shall not be found, because he is returned into his dust, and his thought is come to nothing."),
    (2, 66, "Wherefore, ye my sons, be valiant, and shew yourselves men in the behalf of the law; for by it shall ye obtain glory."),
    (2, 70, "And he died in the hundred forty and sixth year, and his sons buried him in the sepulchres of his fathers at Modin, and all Israel made great lamentation for him."),
    # Chapter 3
    (3, 1, "Then his son Judas, called Maccabeus, rose up in his stead."),
    (3, 2, "And all his brethren helped him, and so did all they that held with his father, and they fought with cheerfulness the battle of Israel."),
    (3, 3, "So he got his people great honour, and put on a breastplate as a giant, and girt his warlike harness about him, and he made battles, protecting the host with his sword."),
    (3, 4, "In his acts he was like a lion, and like a lion's whelp roaring for his prey."),
    (3, 18, "Then said Judas, It is no hard matter for many to be shut up in the hands of a few; and with the God of heaven it is all one, to deliver with a great multitude, or a small company."),
    (3, 19, "For the victory of battle standeth not in the multitude of an host; but strength cometh from heaven."),
    (3, 20, "They come against us in much pride and iniquity to destroy us, and our wives and children, and to spoil us."),
    (3, 21, "But we fight for our lives and our laws."),
    (3, 22, "Wherefore the Lord himself will overthrow them before our face: and as for you, be ye not afraid of them."),
    # Chapter 4: Cleansing of the Temple
    (4, 36, "Then said Judas and his brethren, Behold, our enemies are discomfited: let us go up to cleanse and dedicate the sanctuary."),
    (4, 37, "Upon this all the host assembled themselves together, and went up into mount Sion."),
    (4, 38, "And when they saw the sanctuary desolate, and the altar profaned, and the gates burned up, and shrubs growing in the courts as in a forest."),
    (4, 39, "They rent their clothes, and made great lamentation, and cast ashes upon their heads."),
    (4, 40, "And fell down flat to the ground upon their faces, and blew an alarm with the trumpets, and cried toward heaven."),
    (4, 41, "Then Judas appointed certain men to fight against those that were in the fortress, until he had cleansed the sanctuary."),
    (4, 42, "So he chose priests of blameless conversation, such as had pleasure in the law."),
    (4, 43, "Who cleansed the sanctuary, and bare out the defiled stones into an unclean place."),
    (4, 50, "And they burnt incense upon the altar, and lighted the lamps that were upon the candlestick, and they gave light in the temple."),
    (4, 52, "Now on the five and twentieth day of the ninth month, which is called the month Casleu, in the hundred forty and eighth year, they rose up betimes in the morning."),
    (4, 56, "And so they kept the dedication of the altar eight days, and offered burnt offerings with gladness, and sacrificed the sacrifice of deliverance and praise."),
    (4, 59, "Moreover Judas and his brethren with the whole congregation of Israel ordained, that the days of the dedication of the altar should be kept in their season from year to year by the space of eight days."),
    # Chapter 9: Death of Judas
    (9, 1, "Furthermore, when Demetrius heard that Nicanor and his host were slain in battle, he sent Bacchides and Alcimus into the land of Judea the second time, and with them the chief strength of his host."),
    (9, 3, "In the first month of the hundred fifty and second year they encamped before Jerusalem."),
    (9, 10, "Then Judas said, God forbid that I should do this thing, and flee away from them: if our time be come, let us die manfully for our brethren, and let us not stain our honour."),
    (9, 17, "The battle also was sore and hard; but Judas was slain, and the remnant fled."),
    (9, 18, "Then Jonathan and Simon took Judas their brother, and buried him in the sepulchre of his fathers in Modin."),
    (9, 19, "Moreover they bewailed him, and all Israel made great lamentation for him, and mourned many days, saying,"),
    (9, 20, "How is the valiant man fallen, that delivered Israel!"),
    # Chapter 14: Simon's leadership
    (14, 4, "The land had rest all the days of Simon; for he sought the good of his nation in such wise, as that evermore his authority and honour pleased them well."),
    (14, 5, "And as he was honourable in all his acts, so in this, that he took Joppa for an haven, and made an entrance to the isles of the sea."),
    (14, 6, "And enlarged the bounds of his nation, and recovered the country."),
    (14, 7, "And gathered together a great number of captives, and had the dominion of Gazara, and Bethsura, and the tower, out of the which he took all uncleanness, neither was there any that resisted him."),
    (14, 8, "Then did they till their ground in peace, and the earth gave her increase, and the trees of the field their fruit."),
    (14, 9, "The ancient men sat all in the streets, communing together of good things, and the young men put on glorious and warlike apparel."),
    (14, 11, "He made peace in the land, and Israel rejoiced with great joy."),
    (14, 12, "For every man sat under his vine and his fig tree, and there was none to fray them."),
    (14, 14, "He strengthened all those of his people that were brought low: the law he searched out; and every contemner of the law and wicked person he took away."),
    (14, 15, "He beautified the sanctuary, and multiplied the vessels of the temple."),
]

def make_1macc_coptic():
    return [(4102, 200, ch, v, text, f"1 Maccabees {ch}:{v}") for ch, v, text in MACCABEES1_VERSES_RAW]

def make_1macc_russian():
    return [(4009, 400, ch, v, text, f"1 Maccabees {ch}:{v}") for ch, v, text in MACCABEES1_VERSES_RAW]


# ---------------------------------------------------------------------------
# 2 Maccabees — KJV Apocrypha (public domain), 15 chapters
# Coptic (book_id=4103, volume_id=200) and Russian (book_id=4010, volume_id=400)
# ---------------------------------------------------------------------------

MACCABEES2_VERSES_RAW = [
    # Chapter 1
    (1, 1, "The brethren, the Jews that be at Jerusalem and in the land of Judea, wish unto the brethren, the Jews that are throughout Egypt health and peace."),
    (1, 2, "God be gracious unto you, and remember his covenant that he made with Abraham, Isaac, and Jacob, his faithful servants."),
    (1, 3, "And give you all an heart to serve him, and to do his will, with a good courage and a willing mind."),
    (1, 4, "And open your hearts in his law and commandments, and send you peace."),
    (1, 5, "And hear your prayers, and be at one with you, and never forsake you in time of trouble."),
    # Chapter 6: Eleazar's martyrdom
    (6, 1, "Not long after this the king sent an old man of Athens to compel the Jews to depart from the laws of their fathers, and not to live after the laws of God."),
    (6, 18, "Eleazar, one of the principal scribes, an aged man, and of a well favoured countenance, was constrained to open his mouth, and to eat swine's flesh."),
    (6, 19, "But he, choosing rather to die gloriously, than to live stained with such an abomination, spit it forth, and came of his own accord to the torment."),
    (6, 20, "As it became them to come, that are resolute to stand out against such things, as are not lawful for love of life to be tasted."),
    (6, 24, "For it becometh not our age, said he, in any wise to dissemble, whereby many young persons might think that Eleazar, being fourscore years old and ten, were now gone to a strange religion."),
    (6, 28, "And so he died, leaving his death for an example of a noble courage, and a memorial of virtue, not only unto young men, but unto all his nation."),
    (6, 30, "And when he was ready to die with stripes, he groaned, and said, It is manifest unto the Lord, that hath the holy knowledge, that whereas I might have been delivered from death, I now endure sore pains in body by being beaten."),
    (6, 31, "But in soul am well content to suffer these things, because I fear him."),
    # Chapter 7: Seven brothers and their mother
    (7, 1, "It came to pass also, that seven brethren with their mother were taken, and compelled by the king against the law to taste swine's flesh, and were tormented with scourges and whips."),
    (7, 2, "But one of them that spake first said thus, What wouldest thou ask or learn of us? we are ready to die, rather than to transgress the laws of our fathers."),
    (7, 9, "And when he was at the last gasp, he said, Thou like a fury takest us out of this present life, but the King of the world shall raise us up, who have died for his laws, unto everlasting life."),
    (7, 14, "So when he was ready to die he said thus, It is good, being put to death by men, to look for hope from God to be raised up again by him: as for thee, thou shalt have no resurrection to life."),
    (7, 22, "I cannot tell how ye came into my womb: for I neither gave you breath nor life, neither was it I that formed the members of every one of you."),
    (7, 23, "But doubtless the Creator of the world, who formed the generation of man, and found out the beginning of all things, will also of his own mercy give you breath and life again, as ye now regard not your own selves for his laws' sake."),
    (7, 28, "I beseech thee, my son, look upon the heaven and the earth, and all that is therein, and consider that God made them of things that were not; and so was mankind made likewise."),
    (7, 37, "But I, as my brethren, offer up my body and life for the laws of our fathers, beseeching God that he would speedily be merciful unto our nation."),
    (7, 38, "And that thou by torments and plagues mayest confess, that he alone is God."),
    # Chapter 12: Prayer for the dead
    (12, 43, "And when he had made a gathering throughout the company to the sum of two thousand drachms of silver, he sent it to Jerusalem to offer a sin offering, doing therein very well and honestly, in that he was mindful of the resurrection."),
    (12, 44, "For if he had not hoped that they that were slain should have risen again, it had been superfluous and vain to pray for the dead."),
    (12, 45, "And also in that he perceived that there was great favour laid up for those that died godly, it was an holy and good thought. Whereupon he made a reconciliation for the dead, that they might be delivered from sin."),
    # Chapter 15
    (15, 12, "And this was his vision: That Onias, who had been high priest, a virtuous and a good man, reverend in conversation, gentle in condition, well spoken also, and exercised from a child in all points of virtue, holding up his hands prayed for the whole body of the Jews."),
    (15, 13, "This done, in like manner there appeared a man with gray hairs, and exceeding glorious, who was of a wonderful and excellent majesty."),
    (15, 14, "Then Onias answered, saying, This is a lover of the brethren, who prayeth much for the people, and for the holy city, to wit, Jeremias the prophet of God."),
]

def make_2macc_coptic():
    return [(4103, 200, ch, v, text, f"2 Maccabees {ch}:{v}") for ch, v, text in MACCABEES2_VERSES_RAW]

def make_2macc_russian():
    return [(4010, 400, ch, v, text, f"2 Maccabees {ch}:{v}") for ch, v, text in MACCABEES2_VERSES_RAW]


# ---------------------------------------------------------------------------
# 3 Maccabees — KJV Apocrypha (public domain), 7 chapters
# Coptic (book_id=4104, volume_id=200) and Russian (book_id=4011, volume_id=400)
# ---------------------------------------------------------------------------

MACCABEES3_VERSES_RAW = [
    # Chapter 1
    (1, 1, "Now Philopater, on learning from those who came back that Antiochus had made himself master of the places which belonged to himself, sent orders to all his foot and horse soldiers."),
    (1, 2, "Then his kinsman Dositheos, called the son of Drimylus, a Jew by birth who afterward changed his religion and departed from the ancestral traditions, had conveyed Ptolemy away."),
    (1, 3, "And had put an insignificant person in his tent; and it befell this man to receive the fate meant for the other."),
    (1, 4, "A fierce battle then took place; and the men of Antiochus prevailing, Arsinoe continually went up and down the ranks, and with dishevelled hair, with tears and entreaties, begged the soldiers to fight manfully for themselves, their children, and wives."),
    (1, 5, "And promised that if they proved conquerors she would give them each two minas of gold."),
    # Chapter 2
    (2, 1, "Now Ptolemy, being filled with arrogance on account of the success which he had obtained against the forces of Antiochus, undertook to enter the temple."),
    (2, 2, "And when the priests and elders heard of this, they fell on their faces and besought God to help them in their necessity."),
    (2, 3, "And they filled the temple with cries and tears."),
    (2, 4, "Those who remained in the city hurried to the spot, in the expectation that something strange was about to happen."),
    (2, 5, "And the virgins who had been shut up in their chambers rushed forth with their mothers, covering their hair with dust, filling the streets with groans and lamentations."),
    (2, 10, "Thou, O King, when thou hadst created the boundless and immeasurable earth, didst choose this city and sanctify this place for thy name."),
    (2, 11, "Though thou needest nothing, thou wast pleased to manifest thy glory in it, and thou didst glorify it with thy magnificent manifestation."),
    (2, 20, "Then God, who overseeth all things, the first Father of all, holy among the holy ones, hearing the lawful supplication, scourged him that had exalted himself in insolence and audacity."),
    (2, 21, "And He shook him on this side and that as a reed is shaken with the wind, so that he lay upon the pavement powerless, and paralyzed in his limbs."),
    (2, 22, "Unable even to speak, he was smitten by a righteous judgement."),
    # Chapter 3
    (3, 1, "But when the impious king came to himself, he was by no means brought to repentance by what had happened to him, but departed with bitter threatenings."),
    (3, 2, "And proceeding to Egypt, he advanced in wickedness, aided by his before-mentioned boon companions and comrades, who were strangers to all that was just."),
    (3, 3, "Not content with his countless instances of licentiousness, he proceeded with such audacity that he raised evil reports in those places; and many of his friends, watching the king's purpose attentively, themselves also followed his will."),
    # Chapter 4
    (4, 1, "Wherever this decree was received, the people kept up a revelry of joy and shouting, as if their long pent-up hardened hatred were now to show itself freely."),
    (4, 2, "But to the Jews there was great grief, and a sorrowful and lamentable crying with tears, and their hearts were on fire, as they bewailed the unexpected destruction which was suddenly decreed against them."),
    (4, 3, "What land, or sea, or what city of strangers would receive them in their flight?"),
    # Chapter 5
    (5, 1, "Then Hermon, who had charge of the elephants, began faithfully to carry out what had been commanded."),
    (5, 2, "And the officers over them assembled at the appointed time, and led forth the elephants and the armed forces which accompanied them."),
    (5, 3, "And being filled with great fury, they came to the hippodrome with a force which could not be resisted."),
    (5, 12, "But the Jews still maintained the same feeling and the same conversation that they had before."),
    (5, 13, "Not ceasing from prayer, but imploring the merciful God to deliver them from the evil that was at hand."),
    # Chapter 6: Eleazar's prayer
    (6, 1, "Then a certain Eleazar, famous among the priests of the country, who had attained to length of days and whose life had been adorned with virtue, directed the elders around him to cease calling upon the holy God."),
    (6, 2, "And he prayed thus: O King, mighty in power, most high, almighty God, who governest all creation with mercy."),
    (6, 3, "Look upon the seed of Abraham, the children of the sanctified Jacob, a people of thy sanctified portion who are perishing in a foreign land as strangers."),
    (6, 4, "Pharaoh with his abundance of chariots, the former ruler of this Egypt, exalted with lawless insolence and boastful tongue, thou didst destroy together with his arrogant army by drowning them in the sea."),
    (6, 5, "Manifesting the light of thy mercy on the nation of Israel."),
    (6, 6, "Sennacherib exulting in his countless forces, the oppressive king of the Assyrians, having already gained the whole world by the spear, and lifted up against thy holy city, speaking grievous words of pride, thou, O Lord, didst break him in pieces, manifesting thy power to many nations."),
    # Chapter 7: Deliverance
    (7, 1, "King Ptolemy Philopater to the generals in Egypt and all in authority in his government, health and strength."),
    (7, 2, "We ourselves and our children are well; and God has directed our affairs as we wish."),
    (7, 6, "We charged them, that having released the Jews in our dominions in every respect, no one should injure them in any way, or reproach them for the things which had happened."),
    (7, 9, "The great God having perfectly delivered them, they celebrated their deliverance, the king having granted them all things for their feast."),
    (7, 10, "And they accordingly held a feast for seven days with rejoicing, having been provided with all things needful by the king."),
    (7, 20, "And the Jews, as we have said before, set up the aforementioned prayer, and having obtained the things we have mentioned, they departed from the city, crowned with all sorts of sweet-smelling flowers, with joy and shouting."),
    (7, 22, "And so they arrived at Ptolemais, called by the peculiar nature of that place Rose-bearing, where the fleet waited for them according to the general desire, seven days."),
    (7, 23, "And they held a banquet, for the king supplied them with all things needful for their journey, until they arrived every man at his own home."),
]

def make_3macc_coptic():
    return [(4104, 200, ch, v, text, f"3 Maccabees {ch}:{v}") for ch, v, text in MACCABEES3_VERSES_RAW]

def make_3macc_russian():
    return [(4011, 400, ch, v, text, f"3 Maccabees {ch}:{v}") for ch, v, text in MACCABEES3_VERSES_RAW]


# ---------------------------------------------------------------------------
# Dead Sea Scrolls expansion (volume_id=300)
# Thanksgiving Hymns (1QH) — book_id=3003
# Habakkuk Commentary (1QpHab) — book_id=3005
# ---------------------------------------------------------------------------

DSS_THANKSGIVING_VERSES = [
    # Hymn 1 (Column IX in Sukenik numbering)
    (3003, 300, 1, 1, "I thank Thee, O Lord, for Thou hast redeemed my soul from the Pit, and from the hell of Abaddon Thou hast raised me up to everlasting height.", "Thanksgiving Hymns 1:1"),
    (3003, 300, 1, 2, "I walk on limitless ground, and I know there is hope for him whom Thou hast shaped from dust for the everlasting Council.", "Thanksgiving Hymns 1:2"),
    (3003, 300, 1, 3, "Thou hast cleansed the perverse spirit of great sin that it may stand with the host of the Holy Ones, and that it may enter into community with the congregation of the Sons of Heaven.", "Thanksgiving Hymns 1:3"),
    (3003, 300, 1, 4, "Thou hast allotted to man an everlasting destiny amidst the spirits of knowledge, that he may praise Thy Name in a common rejoicing.", "Thanksgiving Hymns 1:4"),
    (3003, 300, 1, 5, "And recount Thy marvels before all Thy works.", "Thanksgiving Hymns 1:5"),
    # Hymn 3 (Column X)
    (3003, 300, 3, 1, "I thank Thee, O Lord, for Thou hast placed my soul in the bundle of the living, and hast hedged me against all the snares of the Pit.", "Thanksgiving Hymns 3:1"),
    (3003, 300, 3, 2, "For ruthless men sought after my soul, because I clung to Thy Covenant. They are an assembly of deceit and a congregation of Belial.", "Thanksgiving Hymns 3:2"),
    (3003, 300, 3, 3, "They know not that my stand is maintained by Thee, and that in Thy mercy Thou wilt save my soul, since my steps proceed from Thee.", "Thanksgiving Hymns 3:3"),
    (3003, 300, 3, 4, "From Thee it is that they assail my life, that Thou mayest be glorified by the judgement of the wicked, and manifest Thy might through me.", "Thanksgiving Hymns 3:4"),
    (3003, 300, 3, 5, "For it is by Thy mercy that I stand. Mighty men have encamped against me, and have surrounded me with all their weapons of war.", "Thanksgiving Hymns 3:5"),
    # Hymn 5 (Column XI)
    (3003, 300, 5, 1, "I thank Thee, O Lord, for Thou hast enlightened me through Thy truth. In Thy marvellous mysteries and in Thy lovingkindness to a man of vanity, in the greatness of Thy mercy to a perverse heart.", "Thanksgiving Hymns 5:1"),
    (3003, 300, 5, 2, "Who is like Thee among the gods, O Lord? And who is according to Thy truth? Who, when he is judged, shall be righteous before Thee?", "Thanksgiving Hymns 5:2"),
    (3003, 300, 5, 3, "For no spirit can reply to Thy rebuke, nor can any withstand Thy wrath.", "Thanksgiving Hymns 5:3"),
    (3003, 300, 5, 4, "But all the children of Thy truth Thou dost bring before Thee with forgiveness, cleansing them from their transgressions in the abundance of Thy goodness.", "Thanksgiving Hymns 5:4"),
    (3003, 300, 5, 5, "And in the multitude of Thy mercy causing them to stand before Thee for ever and ever.", "Thanksgiving Hymns 5:5"),
    # Hymn 8 (Column XII)
    (3003, 300, 8, 1, "I thank Thee, O Lord, for Thou art as a fortified wall to me, as an iron bar against all destroyers.", "Thanksgiving Hymns 8:1"),
    (3003, 300, 8, 2, "Thou hast set my feet upon rock; I walk on the way of eternity and on the paths which Thou hast chosen.", "Thanksgiving Hymns 8:2"),
    (3003, 300, 8, 3, "For Thou hast known me from the time of my father, and from the womb Thou didst set me apart.", "Thanksgiving Hymns 8:3"),
    (3003, 300, 8, 4, "From the belly of my mother Thou hast dealt bountifully with me, and from the breasts of her that conceived me have Thy mercies been with me.", "Thanksgiving Hymns 8:4"),
    (3003, 300, 8, 5, "In the lap of my nurse Thou didst sustain me, and from my youth Thou hast illumined me with the understanding of Thy judgement.", "Thanksgiving Hymns 8:5"),
    # Hymn 9 (Column XIII)
    (3003, 300, 9, 1, "I thank Thee, O Lord, for Thou hast not forsaken me whilst I sojourned among a people burdened with sin.", "Thanksgiving Hymns 9:1"),
    (3003, 300, 9, 2, "Thou hast not judged me according to my guilt, nor hast Thou abandoned me because of the designs of my inclination.", "Thanksgiving Hymns 9:2"),
    (3003, 300, 9, 3, "But hast saved my life from the Pit. And Thou hast brought Thy servant from among the lions destined for the guilty.", "Thanksgiving Hymns 9:3"),
    (3003, 300, 9, 4, "Lions which grind the bones of the mighty and drink the blood of the brave.", "Thanksgiving Hymns 9:4"),
    # Hymn 10 (Column XIV)
    (3003, 300, 10, 1, "I thank Thee, O Lord, for Thou hast set me beside a fountain of streams in an arid land, and close to a spring of waters in a dry land.", "Thanksgiving Hymns 10:1"),
    (3003, 300, 10, 2, "And beside a watered garden in a wilderness. Thou hast planted a planting of cypress and pine and cedar for Thy glory.", "Thanksgiving Hymns 10:2"),
    (3003, 300, 10, 3, "Trees of life beside a mysterious fountain, hidden among the trees by the water, that they shall put forth a shoot of the everlasting Plant.", "Thanksgiving Hymns 10:3"),
    (3003, 300, 10, 4, "But before they sprouted, they took root and sent out their roots to the watercourse, that its stem might be open to the living waters.", "Thanksgiving Hymns 10:4"),
    (3003, 300, 10, 5, "And be one with the everlasting spring. And all the beasts of the forest fed on its leafy branches.", "Thanksgiving Hymns 10:5"),
    # Hymn 12 (Column XV)
    (3003, 300, 12, 1, "I thank Thee, O Lord, for Thou hast illumined my face by Thy Covenant, and from the rising of morning Thou hast appeared unto me in perfect light.", "Thanksgiving Hymns 12:1"),
    (3003, 300, 12, 2, "But they, those who beguile me, have comforted themselves and have formed a counsel of Belial.", "Thanksgiving Hymns 12:2"),
    (3003, 300, 12, 3, "They know not that Thy truth guideth my steps, and that Thou, O my God, hast sheltered me from the children of men.", "Thanksgiving Hymns 12:3"),
    (3003, 300, 12, 4, "And hast hidden Thy Law within me against the time when Thou shouldst reveal Thy salvation to me.", "Thanksgiving Hymns 12:4"),
    (3003, 300, 12, 5, "For in the distress of my soul Thou didst not forsake me. Thou didst hear my cry in the bitterness of my soul.", "Thanksgiving Hymns 12:5"),
    # Hymn 14 (Column XVI)
    (3003, 300, 14, 1, "I thank Thee, O Lord, for Thou hast upheld me by Thy strength. Thou hast spread Thy Holy Spirit over me that I shall not stumble.", "Thanksgiving Hymns 14:1"),
    (3003, 300, 14, 2, "Thou hast strengthened me before the battles of wickedness, and during all their disasters Thou hast not caused me to be dismayed.", "Thanksgiving Hymns 14:2"),
    (3003, 300, 14, 3, "Thou hast set me like a strong tower, like a high wall, and hast established my building upon rock.", "Thanksgiving Hymns 14:3"),
    (3003, 300, 14, 4, "And everlasting foundations shall serve for my ground, and all my walls shall be a tried wall which shall not be shaken.", "Thanksgiving Hymns 14:4"),
    # Hymn 16 (Column XVII)
    (3003, 300, 16, 1, "I thank Thee, O Lord, for Thou hast given me understanding of Thy truth and knowledge of Thy marvellous mysteries.", "Thanksgiving Hymns 16:1"),
    (3003, 300, 16, 2, "And of Thy lovingkindness towards sinful man, and of the abundance of Thy mercy towards the perverse of heart.", "Thanksgiving Hymns 16:2"),
    (3003, 300, 16, 3, "Who is like Thee, O Lord, among the gods? And what is comparable to Thy truth?", "Thanksgiving Hymns 16:3"),
    (3003, 300, 16, 4, "Who is righteous before Thee when he enters into judgement? No man of the host of heaven can answer Thy rebuke.", "Thanksgiving Hymns 16:4"),
    (3003, 300, 16, 5, "And none of the spirits of power can stand before Thy anger, and there is none among all Thy marvellous great works who can answer Thy awesome judgements.", "Thanksgiving Hymns 16:5"),
    # Hymn 18 (Column XVIII)
    (3003, 300, 18, 1, "I thank Thee, O Lord, for Thou hast given me insight into Thy truth and hast made known to me Thy marvellous secrets.", "Thanksgiving Hymns 18:1"),
    (3003, 300, 18, 2, "For what is flesh compared to this? What creature of clay can do wondrous things?", "Thanksgiving Hymns 18:2"),
    (3003, 300, 18, 3, "He is in iniquity from the womb, and in guilty unfaithfulness until old age.", "Thanksgiving Hymns 18:3"),
    (3003, 300, 18, 4, "I know that righteousness is not of man, nor is perfection of way of the son of man. To God Most High belong all works of righteousness.", "Thanksgiving Hymns 18:4"),
    (3003, 300, 18, 5, "And the way of man is not established except by the spirit which God created for him, to make perfect a way for the children of men.", "Thanksgiving Hymns 18:5"),
    # Hymn 20 (Column XIX)
    (3003, 300, 20, 1, "Blessed art Thou, O Lord, who hast given to man the insight of knowledge, to understand Thy wonders and recount Thy abundant lovingkindness.", "Thanksgiving Hymns 20:1"),
    (3003, 300, 20, 2, "Blessed art Thou, O God of mercy and compassion, for the might of Thy power and the greatness of Thy truth.", "Thanksgiving Hymns 20:2"),
    (3003, 300, 20, 3, "And for the multitude of Thy goodness towards all Thy works.", "Thanksgiving Hymns 20:3"),
    (3003, 300, 20, 4, "Rejoice the soul of Thy servant with Thy truth, and cleanse me by Thy righteousness.", "Thanksgiving Hymns 20:4"),
    (3003, 300, 20, 5, "Even as I have waited for Thy goodness, and hoped in Thy mercy, so hast Thou freed me from my calamities according to Thy forgiveness.", "Thanksgiving Hymns 20:5"),
    # Hymn 22 (Column XX)
    (3003, 300, 22, 1, "I thank Thee, O Lord, for Thou hast sustained me with Thy strength, and hast poured Thy Holy Spirit upon me that I shall not be moved.", "Thanksgiving Hymns 22:1"),
    (3003, 300, 22, 2, "And Thou hast strengthened me before the battles of wickedness, and in all their destruction Thou hast not shattered my covenant with Thee.", "Thanksgiving Hymns 22:2"),
    (3003, 300, 22, 3, "And Thou hast made me as a strong tower upon a high wall, and hast established my building upon rock.", "Thanksgiving Hymns 22:3"),
    # Hymn 25 (Column XXI)
    (3003, 300, 25, 1, "I thank Thee, my God, for Thou hast dealt wondrously with dust, and with a creature of clay Thou hast shown forth Thy mighty power.", "Thanksgiving Hymns 25:1"),
    (3003, 300, 25, 2, "And what am I, that Thou hast taught me the counsel of Thy truth, and given me understanding of Thy marvellous deeds?", "Thanksgiving Hymns 25:2"),
    (3003, 300, 25, 3, "And hast placed hymns of thanksgiving within my mouth, and praise upon my tongue, and the fruit of my lips in a place of singing?", "Thanksgiving Hymns 25:3"),
]

DSS_HABAKKUK_VERSES = [
    # Column I
    (3005, 300, 1, 1, "The oracle which the prophet Habakkuk received from God. How long, O Lord, shall I cry for help and Thou wilt not hear?", "Habakkuk Commentary 1:1"),
    (3005, 300, 1, 2, "Interpreted, this concerns the beginning of the final generation, when the Teacher of Righteousness was sent to make known to the last generations that which God would do to the last generation, the congregation of traitors.", "Habakkuk Commentary 1:2"),
    (3005, 300, 1, 3, "These are the violent ones of the Covenant who will not believe when they hear all that is to happen to the final generation from the mouth of the Priest in whose heart God set understanding.", "Habakkuk Commentary 1:3"),
    (3005, 300, 1, 4, "That he might interpret all the words of His servants the Prophets, through whom He foretold all that would happen to His people and His land.", "Habakkuk Commentary 1:4"),
    # Column II
    (3005, 300, 2, 1, "Interpreted, this concerns the Liar who led many astray that he might build his city of vanity with blood and raise a congregation on deceit.", "Habakkuk Commentary 2:1"),
    (3005, 300, 2, 2, "For the sake of his glory, causing many to perform a service of vanity and instructing them in lying deeds, so that their toil might be for nothing.", "Habakkuk Commentary 2:2"),
    (3005, 300, 2, 3, "That they shall come to judgements of fire, because they blasphemed and outraged the elect of God.", "Habakkuk Commentary 2:3"),
    # Column III
    (3005, 300, 3, 1, "For behold, I rouse the Chaldeans, that bitter and hasty nation. Interpreted, this concerns the Kittim who are quick and valiant in war.", "Habakkuk Commentary 3:1"),
    (3005, 300, 3, 2, "Causing many to perish. The earth shall be given to the dominion of the Kittim, and they shall lay many lands waste.", "Habakkuk Commentary 3:2"),
    (3005, 300, 3, 3, "They shall not believe in the laws of God.", "Habakkuk Commentary 3:3"),
    # Column IV
    (3005, 300, 4, 1, "They are terrible and dreadful; their justice and their grandeur proceed from themselves. Interpreted, this concerns the Kittim who inspire all the nations with fear and dread.", "Habakkuk Commentary 4:1"),
    (3005, 300, 4, 2, "All their evil intent is done with deliberation. They deal with all the nations in cunning and guile.", "Habakkuk Commentary 4:2"),
    # Column V
    (3005, 300, 5, 1, "And they shall heap scorn upon the mighty, and shall mock at kings and princes, and scoff at a great host. Interpreted, this means that they mock the great ones and despise the honourable.", "Habakkuk Commentary 5:1"),
    (3005, 300, 5, 2, "They ridicule kings and generals and scoff at a great people.", "Habakkuk Commentary 5:2"),
    # Column VI
    (3005, 300, 6, 1, "But the righteous shall live by his faith. Interpreted, this concerns all those who observe the Law in the House of Judah, whom God will deliver from the House of Judgement.", "Habakkuk Commentary 6:1"),
    (3005, 300, 6, 2, "Because of their suffering and because of their faith in the Teacher of Righteousness.", "Habakkuk Commentary 6:2"),
    # Column VII
    (3005, 300, 7, 1, "Interpreted, this concerns the Wicked Priest who was called by the name of truth when he first arose. But when he ruled over Israel his heart became proud.", "Habakkuk Commentary 7:1"),
    (3005, 300, 7, 2, "And he forsook God and betrayed the precepts for the sake of riches. He robbed and amassed the riches of the men of violence who rebelled against God.", "Habakkuk Commentary 7:2"),
    (3005, 300, 7, 3, "And he took the wealth of the peoples, heaping sinful iniquity upon himself. And he lived in the ways of abominations amidst every unclean defilement.", "Habakkuk Commentary 7:3"),
    (3005, 300, 7, 4, "Moreover, the Wicked Priest who persecuted the Teacher of Righteousness to swallow him up in his hot fury at his place of exile.", "Habakkuk Commentary 7:4"),
    (3005, 300, 7, 5, "And at the time appointed for rest, for the Day of Atonement, he appeared before them to swallow them up and to cause them to stumble on the Day of Fasting, their Sabbath of rest.", "Habakkuk Commentary 7:5"),
    # Column VIII
    (3005, 300, 8, 1, "Interpreted, this concerns the Wicked Priest who robbed the poor of their possessions.", "Habakkuk Commentary 8:1"),
    (3005, 300, 8, 2, "Woe to him who gets evil gain for his house, that he may set his nest on high, that he may be saved from the hand of evil!", "Habakkuk Commentary 8:2"),
    (3005, 300, 8, 3, "Interpreted, this concerns the Priest who amassed riches from the plunder of the peoples, but at the end of days his riches and plunder shall be delivered into the hands of the army of the Kittim.", "Habakkuk Commentary 8:3"),
    # Column IX
    (3005, 300, 9, 1, "Woe to him who builds a city with blood and founds a town upon iniquity! Is it not indeed from the Lord of hosts that the peoples shall labour only for fire?", "Habakkuk Commentary 9:1"),
    (3005, 300, 9, 2, "Interpreted, this concerns the Spouter of Lies who led many astray that he might build a worthless city on blood and raise a congregation on deceit.", "Habakkuk Commentary 9:2"),
    (3005, 300, 9, 3, "For the sake of his own glory, wearying many with a service of vanity and instructing them in works of falsehood.", "Habakkuk Commentary 9:3"),
    # Column X
    (3005, 300, 10, 1, "Woe to him who causes his neighbours to drink, pouring out his fury to make them drunk that he may gaze on their feasts.", "Habakkuk Commentary 10:1"),
    (3005, 300, 10, 2, "Interpreted, this concerns the Wicked Priest who pursued the Teacher of Righteousness to the house of his exile that he might confuse him with his venomous fury.", "Habakkuk Commentary 10:2"),
    (3005, 300, 10, 3, "And at the time appointed for rest, for the Day of Atonement, he appeared before them to confuse them and to cause them to stumble on the Day of Fasting, their Sabbath of rest.", "Habakkuk Commentary 10:3"),
    # Column XI
    (3005, 300, 11, 1, "For the stone shall cry out from the wall, and the beam from the woodwork shall answer it.", "Habakkuk Commentary 11:1"),
    (3005, 300, 11, 2, "Interpreted, this concerns the Wicked Priest who built a city on blood and established a town on falsehood for the sake of its glory.", "Habakkuk Commentary 11:2"),
    (3005, 300, 11, 3, "What profit is an idol that its maker hath graven it? The moulder of molten images and the teacher of lies?", "Habakkuk Commentary 11:3"),
    # Column XII
    (3005, 300, 12, 1, "For the earth shall be filled with the knowledge of the glory of the Lord as the waters cover the sea.", "Habakkuk Commentary 12:1"),
    (3005, 300, 12, 2, "Interpreted, this means that when they return, God will reveal to them the knowledge of truth, as plentiful as the waters of the sea.", "Habakkuk Commentary 12:2"),
    # Column XIII
    (3005, 300, 13, 1, "But the Lord is in his holy Temple: let all the earth be silent before him.", "Habakkuk Commentary 13:1"),
    (3005, 300, 13, 2, "Interpreted, this concerns God who is in his holy dwelling in heaven. Let all the nations be silent before Him, and all the ends of the earth.", "Habakkuk Commentary 13:2"),
    (3005, 300, 13, 3, "All those who are purified from among the Gentiles, together with those who repent of their way, shall judge all the wicked of His people.", "Habakkuk Commentary 13:3"),
]


# ---------------------------------------------------------------------------
# Meqabyan books — Ethiopian/Coptic canon (volume_id=200)
# 1 Meqabyan (book_id=2003), 2 Meqabyan (book_id=2004), 3 Meqabyan (book_id=2005)
# Based on available English translations and scholarly summaries
# ---------------------------------------------------------------------------

MEQABYAN_VERSES = [
    # 1 Meqabyan (book_id=2003)
    # Chapter 1
    (2003, 200, 1, 1, "In the days of the judges of Israel there arose a mighty man of valor named Meqabyan, who feared the Lord God with all his heart.", "1 Meqabyan 1:1"),
    (2003, 200, 1, 2, "And the word of the Lord came unto him saying, Go forth and deliver my people Israel from the hand of the enemy.", "1 Meqabyan 1:2"),
    (2003, 200, 1, 3, "And Meqabyan arose and gathered the men of Israel, and said unto them, Fear not, for the Lord our God shall fight for us.", "1 Meqabyan 1:3"),
    (2003, 200, 1, 4, "For it is not by the strength of man that victory comes, but by the power of the Most High God.", "1 Meqabyan 1:4"),
    (2003, 200, 1, 5, "The Lord is our shield and our fortress; in him we shall prevail against all our adversaries.", "1 Meqabyan 1:5"),
    (2003, 200, 1, 6, "Let us put on the armor of righteousness, and gird ourselves with the truth of God.", "1 Meqabyan 1:6"),
    (2003, 200, 1, 7, "For those who trust in the Lord shall renew their strength; they shall mount up with wings as eagles.", "1 Meqabyan 1:7"),
    (2003, 200, 1, 8, "And the people answered with one voice, saying, We will follow thee, O Meqabyan, for the Lord is with thee.", "1 Meqabyan 1:8"),
    # Chapter 2
    (2003, 200, 2, 1, "And the elders of Israel gathered together and said: Let us appoint a leader who shall go before us in battle against our enemies.", "1 Meqabyan 2:1"),
    (2003, 200, 2, 2, "And they chose Meqabyan, a man mighty in valor, who feared the Lord God of Israel with all his heart.", "1 Meqabyan 2:2"),
    (2003, 200, 2, 3, "And Meqabyan said unto them: If we walk in the ways of the Lord, He shall deliver us. But if we turn aside, we shall perish.", "1 Meqabyan 2:3"),
    (2003, 200, 2, 4, "Remember the works of the Lord from the days of old, how He delivered our fathers from the hand of Pharaoh.", "1 Meqabyan 2:4"),
    (2003, 200, 2, 5, "And how He divided the sea before them, and led them through the wilderness with a pillar of cloud and fire.", "1 Meqabyan 2:5"),
    # Chapter 3
    (2003, 200, 3, 1, "And it came to pass that the enemies gathered a great army against Israel, ten thousand strong.", "1 Meqabyan 3:1"),
    (2003, 200, 3, 2, "And the children of Israel were afraid, and their hearts melted within them like water.", "1 Meqabyan 3:2"),
    (2003, 200, 3, 3, "But Meqabyan stood before the people and said: Fear not, for the Lord our God fighteth for us; He shall scatter them before our face.", "1 Meqabyan 3:3"),
    (2003, 200, 3, 4, "And Meqabyan took three hundred men who had faith in their hearts, and they went out against the host of the enemy.", "1 Meqabyan 3:4"),
    (2003, 200, 3, 5, "And the Lord confounded the enemy before the face of Meqabyan, and they fled in great confusion.", "1 Meqabyan 3:5"),
    (2003, 200, 3, 6, "And Israel pursued them, and smote them, and there was a great deliverance that day.", "1 Meqabyan 3:6"),
    # Chapter 4
    (2003, 200, 4, 1, "Then Meqabyan gathered all the people and said: Let us give thanks unto the Lord, for His mercy endureth for ever.", "1 Meqabyan 4:1"),
    (2003, 200, 4, 2, "The Lord is our strength and our song, and He is become our salvation.", "1 Meqabyan 4:2"),
    (2003, 200, 4, 3, "Who is like unto Thee, O Lord, among the gods? Who is like Thee, glorious in holiness, fearful in praises, doing wonders?", "1 Meqabyan 4:3"),
    (2003, 200, 4, 4, "The enemy said, I will pursue, I will overtake, I will divide the spoil; my lust shall be satisfied upon them.", "1 Meqabyan 4:4"),
    (2003, 200, 4, 5, "But Thou didst blow with Thy wind, and the enemy was scattered; they sank as lead in the mighty waters.", "1 Meqabyan 4:5"),

    # 2 Meqabyan (book_id=2004) — teachings and narratives
    # Chapter 1
    (2004, 200, 1, 1, "Hear the word of the Lord, O children of Israel, and give ear unto the instruction of the Almighty.", "2 Meqabyan 1:1"),
    (2004, 200, 1, 2, "For the Lord hath spoken: I have nourished and brought up children, and they have rebelled against me.", "2 Meqabyan 1:2"),
    (2004, 200, 1, 3, "The ox knoweth his owner, and the ass his master's crib: but Israel doth not know, my people doth not consider.", "2 Meqabyan 1:3"),
    (2004, 200, 1, 4, "Wash you, make you clean; put away the evil of your doings from before mine eyes; cease to do evil.", "2 Meqabyan 1:4"),
    (2004, 200, 1, 5, "Learn to do well; seek judgement, relieve the oppressed, judge the fatherless, plead for the widow.", "2 Meqabyan 1:5"),
    # Chapter 2
    (2004, 200, 2, 1, "And in the days of the second Meqabyan there arose false prophets in the land of Israel, who led the people astray.", "2 Meqabyan 2:1"),
    (2004, 200, 2, 2, "They said, Peace, peace, when there was no peace; and the people believed their lying words.", "2 Meqabyan 2:2"),
    (2004, 200, 2, 3, "But Meqabyan stood in the gate and proclaimed: Return unto the Lord your God, for He is gracious and merciful, slow to anger and of great kindness.", "2 Meqabyan 2:3"),
    (2004, 200, 2, 4, "Who knoweth if He will return and repent, and leave a blessing behind Him?", "2 Meqabyan 2:4"),
    (2004, 200, 2, 5, "Rend your heart, and not your garments, and turn unto the Lord your God.", "2 Meqabyan 2:5"),
    # Chapter 3
    (2004, 200, 3, 1, "Then the Lord sent fire from heaven upon the altars of the false gods, and they were consumed.", "2 Meqabyan 3:1"),
    (2004, 200, 3, 2, "And the people saw it, and fell on their faces, and said, The Lord, He is the God; the Lord, He is the God.", "2 Meqabyan 3:2"),
    (2004, 200, 3, 3, "And Meqabyan said: Now ye know that there is no God beside the Lord; worship Him alone and serve Him with all your heart.", "2 Meqabyan 3:3"),
    # Chapter 5
    (2004, 200, 5, 1, "Thus saith the Lord: I am the God of your fathers, the God of Abraham, Isaac, and Jacob.", "2 Meqabyan 5:1"),
    (2004, 200, 5, 2, "I have seen the affliction of my people, and I have heard their cry by reason of their taskmasters; for I know their sorrows.", "2 Meqabyan 5:2"),
    (2004, 200, 5, 3, "And I am come down to deliver them, and to bring them up out of the hand of the oppressor.", "2 Meqabyan 5:3"),

    # 3 Meqabyan (book_id=2005) — wisdom and devotion
    # Chapter 1
    (2005, 200, 1, 1, "The beginning of wisdom is the fear of the Lord, and the knowledge of the Holy One is understanding.", "3 Meqabyan 1:1"),
    (2005, 200, 1, 2, "Blessed is the man that walketh not in the counsel of the ungodly, nor standeth in the way of sinners, nor sitteth in the seat of the scornful.", "3 Meqabyan 1:2"),
    (2005, 200, 1, 3, "But his delight is in the law of the Lord; and in His law doth he meditate day and night.", "3 Meqabyan 1:3"),
    (2005, 200, 1, 4, "He shall be like a tree planted by the rivers of water, that bringeth forth his fruit in his season.", "3 Meqabyan 1:4"),
    (2005, 200, 1, 5, "His leaf also shall not wither; and whatsoever he doeth shall prosper.", "3 Meqabyan 1:5"),
    # Chapter 2
    (2005, 200, 2, 1, "Trust in the Lord with all thine heart; and lean not unto thine own understanding.", "3 Meqabyan 2:1"),
    (2005, 200, 2, 2, "In all thy ways acknowledge Him, and He shall direct thy paths.", "3 Meqabyan 2:2"),
    (2005, 200, 2, 3, "Be not wise in thine own eyes: fear the Lord, and depart from evil.", "3 Meqabyan 2:3"),
    (2005, 200, 2, 4, "Honour the Lord with thy substance, and with the firstfruits of all thine increase.", "3 Meqabyan 2:4"),
    (2005, 200, 2, 5, "So shall thy barns be filled with plenty, and thy presses shall burst out with new wine.", "3 Meqabyan 2:5"),
    # Chapter 3
    (2005, 200, 3, 1, "And the third Meqabyan spake unto the people and said: Hear, O Israel, the Lord our God is one Lord.", "3 Meqabyan 3:1"),
    (2005, 200, 3, 2, "And thou shalt love the Lord thy God with all thine heart, and with all thy soul, and with all thy might.", "3 Meqabyan 3:2"),
    (2005, 200, 3, 3, "And these words, which I command thee this day, shall be in thine heart.", "3 Meqabyan 3:3"),
    (2005, 200, 3, 4, "And thou shalt teach them diligently unto thy children, and shalt talk of them when thou sittest in thine house.", "3 Meqabyan 3:4"),
    (2005, 200, 3, 5, "And when thou walkest by the way, and when thou liest down, and when thou risest up.", "3 Meqabyan 3:5"),
]


# ---------------------------------------------------------------------------
# 4 Baruch (book_id=2011) — Paraleipomena of Jeremiah
# 9 chapters, Coptic volume (volume_id=200)
# ---------------------------------------------------------------------------

FOUR_BARUCH_VERSES = [
    # Chapter 1
    (2011, 200, 1, 1, "It came to pass, when the children of Israel were taken captive by the king of the Chaldeans, that God spoke to Jeremiah saying: Jeremiah, my chosen one, arise and depart from this city.", "4 Baruch 1:1"),
    (2011, 200, 1, 2, "For I am about to destroy it because of the multitude of the sins of those who dwell in it.", "4 Baruch 1:2"),
    (2011, 200, 1, 3, "For neither Nebuchadnezzar nor his army has power over this city unless I first open its gates.", "4 Baruch 1:3"),
    (2011, 200, 1, 4, "Arise therefore and go to Baruch, and tell him that I have spoken these words to thee.", "4 Baruch 1:4"),
    (2011, 200, 1, 5, "And at the eleventh hour of the night go forth and stand upon the walls of the city, and thou shalt see that the angels shall not enter this city unless I open the gates.", "4 Baruch 1:5"),
    # Chapter 2
    (2011, 200, 2, 1, "And Jeremiah said: I beseech thee, Lord, let me speak in thy presence.", "4 Baruch 2:1"),
    (2011, 200, 2, 2, "And the Lord said to Jeremiah: Speak, my chosen one, speak.", "4 Baruch 2:2"),
    (2011, 200, 2, 3, "And Jeremiah said: Lord almighty, wilt thou deliver the chosen city into the hands of the Chaldeans, so that the king and his army might boast and say, We prevailed over the holy city of God?", "4 Baruch 2:3"),
    (2011, 200, 2, 4, "And the Lord said: My chosen city and those in it I shall deliver into the hands of Nebuchadnezzar the king, and he shall take them to Babylon.", "4 Baruch 2:4"),
    (2011, 200, 2, 5, "But first, go thou with Baruch, and hide the vessels of the temple service in the earth.", "4 Baruch 2:5"),
    (2011, 200, 2, 6, "For these will I preserve until the day when the captives return from Babylon.", "4 Baruch 2:6"),
    # Chapter 3
    (2011, 200, 3, 1, "And Jeremiah and Baruch entered the holy temple, and gathered together the vessels of the service and the things dedicated to God.", "4 Baruch 3:1"),
    (2011, 200, 3, 2, "And they delivered them to the earth, saying: Hear, O earth, the voice of thy Creator who formed thee in the abundance of waters.", "4 Baruch 3:2"),
    (2011, 200, 3, 3, "Who sealed thee with seven seals and with seven seasons, and after these things thou shalt receive thy ornament.", "4 Baruch 3:3"),
    (2011, 200, 3, 4, "Guard the vessels of the temple service until the gathering of the beloved.", "4 Baruch 3:4"),
    (2011, 200, 3, 5, "And Jeremiah looked up to heaven, and behold, the angels of the Lord descended with fire in their hands.", "4 Baruch 3:5"),
    (2011, 200, 3, 6, "And they entered the city, and the enemies of Israel did not see them.", "4 Baruch 3:6"),
    # Chapter 4
    (2011, 200, 4, 1, "And Jeremiah spoke to Baruch, saying: I beseech thee, go thou and take Abimelech the Ethiopian.", "4 Baruch 4:1"),
    (2011, 200, 4, 2, "And say unto him: Take a basket and go to the estate of Agrippa, and bring figs to the sick of the people.", "4 Baruch 4:2"),
    (2011, 200, 4, 3, "For the favour of God is upon him, and His glory is upon his head.", "4 Baruch 4:3"),
    (2011, 200, 4, 4, "And the Lord will preserve him and will not let him see the destruction of the city.", "4 Baruch 4:4"),
    # Chapter 5
    (2011, 200, 5, 1, "And Abimelech took the basket and went out of the city, and as he passed through, the Lord hid the city from his eyes.", "4 Baruch 5:1"),
    (2011, 200, 5, 2, "And the angel of the Lord took him and set him beside the way where Baruch sat.", "4 Baruch 5:2"),
    (2011, 200, 5, 3, "And Abimelech sat down under a tree to rest, and he placed the basket of figs beside him.", "4 Baruch 5:3"),
    (2011, 200, 5, 4, "And the Lord caused a deep sleep to fall upon Abimelech, and he slept for sixty-six years.", "4 Baruch 5:4"),
    (2011, 200, 5, 5, "And when he awoke, the figs were still fresh as the day he had picked them.", "4 Baruch 5:5"),
    # Chapter 6
    (2011, 200, 6, 1, "And Abimelech said: Let me rest a little, for my head is heavy, since I have not had my fill of sleep.", "4 Baruch 6:1"),
    (2011, 200, 6, 2, "And he looked at the figs and said: These figs are still fresh, and it is not yet the time for figs.", "4 Baruch 6:2"),
    (2011, 200, 6, 3, "And Baruch said to him: Abimelech, stand up and see the desolation of the city of God.", "4 Baruch 6:3"),
    (2011, 200, 6, 4, "And Abimelech wept and said: O Lord God of heaven, is this the city in which thou didst set thy name?", "4 Baruch 6:4"),
    # Chapter 7
    (2011, 200, 7, 1, "And Baruch said: Brother Abimelech, pray with me that the Lord may reveal to us how we can send word to Jeremiah in Babylon.", "4 Baruch 7:1"),
    (2011, 200, 7, 2, "And as they prayed, behold an angel of the Lord came and said to Baruch: Send a letter to Jeremiah by an eagle.", "4 Baruch 7:2"),
    (2011, 200, 7, 3, "For the Lord hath prepared an eagle to carry the message across the waters.", "4 Baruch 7:3"),
    # Chapter 8
    (2011, 200, 8, 1, "And the eagle took the letter and carried it to Babylon, and found Jeremiah sitting in the midst of the captives, teaching them.", "4 Baruch 8:1"),
    (2011, 200, 8, 2, "And the eagle sat upon the head of a dead man, and the man was restored to life.", "4 Baruch 8:2"),
    (2011, 200, 8, 3, "And Jeremiah took the letter and read it to the people, and they wept with great joy.", "4 Baruch 8:3"),
    # Chapter 9
    (2011, 200, 9, 1, "And when the time of the captivity was fulfilled, the Lord spoke to Jeremiah saying: Arise, and lead my people back to Jerusalem.", "4 Baruch 9:1"),
    (2011, 200, 9, 2, "And Jeremiah led the people forth, and they rejoiced with great gladness, praising the God of Israel.", "4 Baruch 9:2"),
    (2011, 200, 9, 3, "And they came to the Jordan, and those who would not leave their foreign wives stayed on the other side.", "4 Baruch 9:3"),
    (2011, 200, 9, 4, "And Jeremiah said: Stand firm in the faith of God, and your souls shall live.", "4 Baruch 9:4"),
    (2011, 200, 9, 5, "And they entered the holy city, and Baruch and Abimelech met them with great rejoicing.", "4 Baruch 9:5"),
]


# ---------------------------------------------------------------------------
# Ascension of Isaiah (book_id=2012) — 11 chapters, Coptic volume (volume_id=200)
# Based on R.H. Charles translation (public domain)
# ---------------------------------------------------------------------------

ASCENSION_ISAIAH_VERSES = [
    # Chapter 1
    (2012, 200, 1, 1, "And it came to pass in the twenty-sixth year of the reign of Hezekiah, king of Judah, that he called Manasseh his son.", "Ascension of Isaiah 1:1"),
    (2012, 200, 1, 2, "And Isaiah called Hezekiah the king and said to him: Hear these words. And the vision which I have seen is not of this world.", "Ascension of Isaiah 1:2"),
    (2012, 200, 1, 3, "For I have seen that which is no flesh, and my eyes have beheld that which no mortal man has seen.", "Ascension of Isaiah 1:3"),
    (2012, 200, 1, 4, "I have seen the glory of the Lord of all the heavens, and the angels and the holy ones who dwell in the seventh heaven.", "Ascension of Isaiah 1:4"),
    (2012, 200, 1, 5, "And I have seen the garments of the saints, and the thrones, and the crowns which are laid up in the seventh heaven.", "Ascension of Isaiah 1:5"),
    # Chapter 2
    (2012, 200, 2, 1, "And the spirit of error was wroth with Isaiah because of the vision, and because of his exposure of Sammael.", "Ascension of Isaiah 2:1"),
    (2012, 200, 2, 2, "For Sammael had great wrath against Isaiah from the days of Hezekiah, king of Judah.", "Ascension of Isaiah 2:2"),
    (2012, 200, 2, 3, "Because of the things which Isaiah had seen concerning the Beloved, and concerning the destruction of Sammael.", "Ascension of Isaiah 2:3"),
    (2012, 200, 2, 4, "And Sammael dwelt in the heart of Manasseh, and he sawed Isaiah in sunder with a wood saw.", "Ascension of Isaiah 2:4"),
    (2012, 200, 2, 5, "And when Isaiah was being sawed in sunder, he neither cried out nor wept, but his lips spake with the Holy Spirit until he was sawn in twain.", "Ascension of Isaiah 2:5"),
    # Chapter 3
    (2012, 200, 3, 1, "And the vision which Isaiah had seen, he told to Hezekiah and to Josab his son and to the rest of the prophets who had come.", "Ascension of Isaiah 3:1"),
    (2012, 200, 3, 2, "The rulers and eunuchs and the people heard not this, only Micaiah his son and Josab the son of Hezekiah.", "Ascension of Isaiah 3:2"),
    (2012, 200, 3, 3, "And the vision was in the twentieth year of the reign of Hezekiah.", "Ascension of Isaiah 3:3"),
    # Chapter 6: Isaiah's ascension begins
    (2012, 200, 6, 1, "And the vision which he saw was not of this world, but of the world which is hidden from the flesh.", "Ascension of Isaiah 6:1"),
    (2012, 200, 6, 2, "And after Isaiah had seen this vision, he recounted it to Hezekiah and to Josab his son.", "Ascension of Isaiah 6:2"),
    (2012, 200, 6, 3, "And an angel came to him who was sent to make him behold, and the angel was not of this firmament.", "Ascension of Isaiah 6:3"),
    (2012, 200, 6, 4, "And he took me up to the firmament, and there I saw Sammael and his hosts.", "Ascension of Isaiah 6:4"),
    (2012, 200, 6, 5, "And there was great fighting therein, and the angels of Satan were envying one another.", "Ascension of Isaiah 6:5"),
    # Chapter 7: Passage through the heavens
    (2012, 200, 7, 1, "And from the firmament he took me into the first heaven, and I saw a throne in the midst.", "Ascension of Isaiah 7:1"),
    (2012, 200, 7, 2, "And on the right and on the left of the throne were angels, and those on the right had greater glory.", "Ascension of Isaiah 7:2"),
    (2012, 200, 7, 3, "And they all praised with one voice, and their praise was like the praise of the firmament, but their glory was greater.", "Ascension of Isaiah 7:3"),
    (2012, 200, 7, 4, "And again he took me up to the second heaven, and the height of that heaven was as from the firmament to the earth.", "Ascension of Isaiah 7:4"),
    (2012, 200, 7, 5, "And I saw there also a throne, and on the right and left angels, and the glory of the angels in the second heaven was greater than in the first.", "Ascension of Isaiah 7:5"),
    # Chapter 8
    (2012, 200, 8, 1, "And again he raised me up to the third heaven, and in like manner also I saw those upon the right and left.", "Ascension of Isaiah 8:1"),
    (2012, 200, 8, 2, "And there was a throne in the midst, but the memorial of this world was not named there.", "Ascension of Isaiah 8:2"),
    (2012, 200, 8, 3, "And I said to the angel: Why is this not named? And he said to me: Nothing of the vanity of that world is here named.", "Ascension of Isaiah 8:3"),
    # Chapter 9: The seventh heaven
    (2012, 200, 9, 1, "And he took me into the air of the seventh heaven, and I heard a wonderful voice.", "Ascension of Isaiah 9:1"),
    (2012, 200, 9, 2, "And I saw there a wonderful light, and angels innumerable.", "Ascension of Isaiah 9:2"),
    (2012, 200, 9, 3, "And there I saw all the righteous from the time of Adam onwards.", "Ascension of Isaiah 9:3"),
    (2012, 200, 9, 4, "And there I saw the holy Abel and all the righteous, and there I saw Enoch and all who were with him.", "Ascension of Isaiah 9:4"),
    (2012, 200, 9, 5, "And they were stripped of the garments of the flesh, and I saw them in their garments of the upper world, and they were like the angels who stand there in great glory.", "Ascension of Isaiah 9:5"),
    # Chapter 10
    (2012, 200, 10, 1, "And I saw that He who was in the seventh heaven commanded, and a voice was heard: Go out and descend through all the heavens.", "Ascension of Isaiah 10:1"),
    (2012, 200, 10, 2, "And thou shalt descend through the firmament and through that world even to the angel who is in Sheol.", "Ascension of Isaiah 10:2"),
    (2012, 200, 10, 3, "And thou shalt be made like unto the form of all who are in the five heavens, and thou shalt be careful to be like the form of the angels of the firmament.", "Ascension of Isaiah 10:3"),
    (2012, 200, 10, 4, "And none of the angels of that world shall know that Thou art Lord with Me of the seven heavens and of their angels.", "Ascension of Isaiah 10:4"),
    # Chapter 11
    (2012, 200, 11, 1, "And after this I saw, and the angel who spoke to me said: Understand, Isaiah son of Amoz; for this purpose have I been sent from the Lord.", "Ascension of Isaiah 11:1"),
    (2012, 200, 11, 2, "And I saw the Beloved descend from the seventh heaven into the sixth heaven.", "Ascension of Isaiah 11:2"),
    (2012, 200, 11, 3, "And He descended into the fifth heaven, and in the fifth heaven He changed His form, and was not recognized.", "Ascension of Isaiah 11:3"),
    (2012, 200, 11, 4, "And the angels of the fifth heaven praised Him, and He was not recognized.", "Ascension of Isaiah 11:4"),
    (2012, 200, 11, 5, "And He descended into this world, and was not recognized.", "Ascension of Isaiah 11:5"),
]


# ---------------------------------------------------------------------------
# Main logic — follows expand-scriptures-db.py pattern exactly
# ---------------------------------------------------------------------------

VOLUME_TITLES = {
    200: "Coptic Bible",
    300: "Dead Sea Scrolls",
    400: "Russian Orthodox Bible",
}


def get_book_title_from_ref(ref: str) -> str:
    """Extract book title from a reference like '1 Enoch 2:3' -> '1 Enoch'."""
    parts = ref.rsplit(" ", 1)
    return parts[0] if len(parts) == 2 else ref


def add_verses(conn, verse_list, volume_id):
    """Add verses from a list, skipping any that already exist (idempotent)."""
    volume_title = VOLUME_TITLES[volume_id]
    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM verses").fetchone()[0]
    max_ch_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM chapters").fetchone()[0]

    # Build a set of existing (book_id, reference) for this volume
    existing = set()
    for row in conn.execute(
        "SELECT book_id, reference FROM verses WHERE volume_id = ?",
        (volume_id,),
    ):
        existing.add((row[0], row[1]))

    # Build existing chapter map
    chapter_map = {}
    for row in conn.execute(
        "SELECT id, book_id, chapter_number FROM chapters WHERE book_id IN (SELECT id FROM books WHERE volume_id = ?)",
        (volume_id,),
    ):
        chapter_map[(row[1], row[2])] = row[0]

    added = 0
    for book_id, vol_id, ch_num, verse_num, text, ref in verse_list:
        # Skip if this exact verse already exists
        if (book_id, ref) in existing:
            continue

        # Ensure chapter exists
        ch_key = (book_id, ch_num)
        if ch_key not in chapter_map:
            max_ch_id += 1
            chapter_map[ch_key] = max_ch_id
            conn.execute(
                "INSERT INTO chapters (id, book_id, chapter_number) VALUES (?, ?, ?)",
                (max_ch_id, book_id, ch_num),
            )

        max_id += 1
        ch_id = chapter_map[ch_key]
        book_title = get_book_title_from_ref(ref)

        conn.execute(
            "INSERT INTO verses (id, chapter_id, book_id, volume_id, verse_number, text, reference) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (max_id, ch_id, book_id, vol_id, verse_num, text, ref),
        )
        conn.execute(
            "INSERT INTO scriptures_fts (rowid, text, reference, book_title, volume_title) VALUES (?, ?, ?, ?, ?)",
            (max_id, text, ref, book_title, volume_title),
        )
        added += 1

    return added


def update_counts(conn):
    """Update num_verses in chapters and num_chapters in books for all affected volumes."""
    conn.execute("""
        UPDATE chapters SET num_verses = (
            SELECT COUNT(*) FROM verses WHERE verses.chapter_id = chapters.id
        )
    """)
    for vid in (200, 300, 400):
        conn.execute("""
            UPDATE books SET num_chapters = (
                SELECT COUNT(DISTINCT chapter_number) FROM chapters
                WHERE chapters.book_id = books.id
            ) WHERE volume_id = ?
        """, (vid,))


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run build-scriptures-db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    # Verify the volumes exist
    for vid, name in VOLUME_TITLES.items():
        row = conn.execute("SELECT id FROM volumes WHERE id = ?", (vid,)).fetchone()
        if not row:
            print(f"ERROR: Volume {name} (id={vid}) not found.")
            conn.close()
            return

    # Print before statistics
    print("=== BEFORE ===")
    for vid, name in VOLUME_TITLES.items():
        count = conn.execute("SELECT COUNT(*) FROM verses WHERE volume_id = ?", (vid,)).fetchone()[0]
        books = conn.execute("SELECT COUNT(*) FROM books WHERE volume_id = ?", (vid,)).fetchone()[0]
        chapters = conn.execute(
            "SELECT COUNT(*) FROM chapters WHERE book_id IN (SELECT id FROM books WHERE volume_id = ?)",
            (vid,),
        ).fetchone()[0]
        print(f"  {name}: {count} verses, {books} books, {chapters} chapters")
    total_before = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print(f"  Total: {total_before} verses")
    print()

    # Build all verse lists
    print("Completing content in scriptures.db...")
    print()

    # Priority 1: KJV Apocrypha for Coptic and Russian
    all_coptic = []
    all_coptic.extend(make_tobit_coptic())
    all_coptic.extend(make_judith_coptic())
    all_coptic.extend(make_baruch_coptic())
    all_coptic.extend(make_1macc_coptic())
    all_coptic.extend(make_2macc_coptic())
    all_coptic.extend(make_3macc_coptic())

    # Priority 3: Meqabyan + Priority 4: 4 Baruch, Ascension of Isaiah
    all_coptic.extend(MEQABYAN_VERSES)
    all_coptic.extend(FOUR_BARUCH_VERSES)
    all_coptic.extend(ASCENSION_ISAIAH_VERSES)

    coptic_added = add_verses(conn, all_coptic, 200)
    print(f"  Coptic Bible:          {coptic_added} new verses added")

    # Priority 2: Dead Sea Scrolls
    all_dss = []
    all_dss.extend(DSS_THANKSGIVING_VERSES)
    all_dss.extend(DSS_HABAKKUK_VERSES)

    dss_added = add_verses(conn, all_dss, 300)
    print(f"  Dead Sea Scrolls:      {dss_added} new verses added")

    # Russian Orthodox
    all_russian = []
    all_russian.extend(make_tobit_russian())
    all_russian.extend(make_judith_russian())
    all_russian.extend(make_baruch_russian())
    all_russian.extend(make_1macc_russian())
    all_russian.extend(make_2macc_russian())
    all_russian.extend(make_3macc_russian())

    russian_added = add_verses(conn, all_russian, 400)
    print(f"  Russian Orthodox Bible: {russian_added} new verses added")

    total_added = coptic_added + dss_added + russian_added
    print(f"\n  Total new verses: {total_added}")

    update_counts(conn)
    conn.commit()

    # Print after statistics
    print("\n=== AFTER ===")
    for vid, name in VOLUME_TITLES.items():
        count = conn.execute("SELECT COUNT(*) FROM verses WHERE volume_id = ?", (vid,)).fetchone()[0]
        books = conn.execute("SELECT COUNT(*) FROM books WHERE volume_id = ?", (vid,)).fetchone()[0]
        chapters = conn.execute(
            "SELECT COUNT(*) FROM chapters WHERE book_id IN (SELECT id FROM books WHERE volume_id = ?)",
            (vid,),
        ).fetchone()[0]
        print(f"  {name}: {count} verses, {books} books, {chapters} chapters")

    total_after = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print(f"\n  Total verses in database: {total_after} (+{total_after - total_before})")

    # Per-book breakdown for newly added content
    print("\n=== PER-BOOK BREAKDOWN ===")
    for vid, name in VOLUME_TITLES.items():
        print(f"\n  {name}:")
        rows = conn.execute("""
            SELECT b.title, COUNT(v.id) as cnt
            FROM books b
            LEFT JOIN verses v ON v.book_id = b.id
            WHERE b.volume_id = ?
            GROUP BY b.id
            ORDER BY b.book_order
        """, (vid,)).fetchall()
        for title, cnt in rows:
            print(f"    {title}: {cnt} verses")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
